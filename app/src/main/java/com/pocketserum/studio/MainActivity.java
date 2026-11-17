package com.pocketserum.studio;

import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.content.ActivityNotFoundException;
import android.graphics.Color;
import android.graphics.Insets;
import android.os.Build;
import android.view.WindowInsets;
import android.widget.FrameLayout;
import android.net.Uri;
import android.util.Base64;
import android.util.Log;
import android.webkit.ConsoleMessage;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.ValueCallback;
import android.widget.Toast;
import java.io.OutputStream;

public class MainActivity extends Activity {
    private static final String TAG = "PulseStudio";
    private static final int REQUEST_OPEN = 101;
    private static final int REQUEST_SAVE = 102;
    private WebView webView;
    private ValueCallback<Uri[]> fileCallback;
    private byte[] pendingSave;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(18,22,29));
        getWindow().setNavigationBarColor(Color.rgb(18,22,29));
        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(18,22,29));
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(18,22,29));
        root.setOnApplyWindowInsetsListener((view, insets) -> {
            int left, top, right, bottom;
            if (Build.VERSION.SDK_INT >= 30) {
                Insets bars = insets.getInsets(WindowInsets.Type.systemBars());
                left=bars.left;top=bars.top;right=bars.right;bottom=bars.bottom;
            } else {
                left=insets.getSystemWindowInsetLeft();
                top=insets.getSystemWindowInsetTop();
                right=insets.getSystemWindowInsetRight();
                bottom=insets.getSystemWindowInsetBottom();
            }
            view.setPadding(left,top,right,bottom);
            return insets;
        });
        root.addView(webView, new FrameLayout.LayoutParams(-1, -1));
        setContentView(root);
        WebSettings settings=webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        webView.setWebViewClient(new WebViewClient() {
            @Override public void onPageFinished(WebView view, String url) {
                Log.i(TAG, "Page loaded: " + url);
                view.evaluateJavascript("(function(){try{return JSON.stringify({ready:typeof boot==='function',notes:state.notes.length,effects:document.querySelectorAll('#effectsGrid .panel').length,keys:document.querySelectorAll('#keyboard .white-key').length,canvas:document.getElementById('grid').width})}catch(e){return 'ERROR:'+e.message}})()", result -> Log.i(TAG, "STARTUP TEST: " + result));
                if (getIntent().getBooleanExtra("smokeTest", false)) {
                    view.evaluateJavascript("(async function(){try{var ctx=new OfflineAudioContext(2,44100*2,44100);var bus=makeAudioGraph(ctx);scheduleNote(ctx,bus,{pitch:72,vel:.9},0.01,0.4);var b=await ctx.startRendering();var d=b.getChannelData(0);var sum=0;for(var i=0;i<d.length;i++)sum+=Math.abs(d[i]);var wav=wavBytes(b);var mp3=encodeMp3(b);if(wav.length<100||mp3.length<100)throw new Error('Export empty');document.querySelector('[data-tab=effects]').click();if(!document.getElementById('effectsView').classList.contains('active'))throw new Error('Effects tab failed');document.querySelector('[data-tab=roll]').click();console.log('SMOKE_EXPORT WAV_BYTES '+wav.length+' MP3_BYTES '+mp3.length);console.log('SMOKE_AUDIO_MEAN '+(sum/d.length).toFixed(6));}catch(e){console.error('SMOKE_AUDIO_FAIL '+e.message)}})()", null);
                }
            }
        });
        webView.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onConsoleMessage(ConsoleMessage message) {
                Log.i(TAG, "JS " + message.messageLevel().name() + " " + message.message() + " (" + message.lineNumber() + ")");
                return true;
            }
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> cb, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback=cb;
                try {
                    Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
                    intent.setType("*/*");
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    startActivityForResult(intent,REQUEST_OPEN);
                    return true;
                } catch (ActivityNotFoundException ex) {
                    fileCallback=null;
                    Toast.makeText(MainActivity.this,"No file picker available",Toast.LENGTH_SHORT).show();
                    return false;
                }
            }
        });
        webView.addJavascriptInterface(new Bridge(),"Android");
        webView.loadUrl("file:///android_asset/index.html");
    }

    private class Bridge {
        @JavascriptInterface public void saveBase64(String filename,String mime,String base64) {
            if (base64.length() > 160_000_000) return;
            try {
                byte[] bytes=Base64.decode(base64,Base64.DEFAULT);
                runOnUiThread(()->openSaveDialog(filename,mime,bytes));
            } catch(Exception e) {runOnUiThread(()->Toast.makeText(MainActivity.this,"Export failed: "+e.getMessage(),Toast.LENGTH_LONG).show());}
        }
    }
    private void openSaveDialog(String filename,String mime,byte[] bytes) {
        pendingSave=bytes;
        Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType(mime);
        intent.putExtra(Intent.EXTRA_TITLE, filename);
        intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
        try {startActivityForResult(intent,REQUEST_SAVE);} catch(Exception e) {pendingSave=null; Toast.makeText(this,"Can't open save dialog",Toast.LENGTH_SHORT).show();}
    }
    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data) {
        super.onActivityResult(requestCode,resultCode,data);
        if (requestCode==REQUEST_OPEN) {
            if(fileCallback!=null) {
                Uri[] uris=resultCode==RESULT_OK&&data!=null&&data.getData()!=null?new Uri[]{data.getData()}:null;
                fileCallback.onReceiveValue(uris); fileCallback=null;
            }
        } else if (requestCode==REQUEST_SAVE) {
            if(resultCode==RESULT_OK&&data!=null&&data.getData()!=null&&pendingSave!=null){
                byte[] bytes=pendingSave;Uri target=data.getData();
                new Thread(()->{
                    try(OutputStream os=getContentResolver().openOutputStream(target,"w")){
                        if(os==null)throw new Exception("No output stream");
                        os.write(bytes);os.flush();
                        runOnUiThread(()->Toast.makeText(this,"File saved",Toast.LENGTH_SHORT).show());
                    }catch(Exception e){runOnUiThread(()->Toast.makeText(this,"Save error: "+e.getMessage(),Toast.LENGTH_LONG).show());}
                }).start();
            }
            pendingSave=null;
        }
    }
    @Override protected void onDestroy() {
        if(webView!=null){webView.loadUrl("about:blank");webView.destroy();webView=null;}
        super.onDestroy();
    }
}
