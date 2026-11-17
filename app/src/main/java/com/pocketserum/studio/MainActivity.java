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
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.file.Files;
import java.net.HttpURLConnection;
import java.net.URL;

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
                    view.evaluateJavascript("(async function(){try{var play=document.getElementById('play');var rect=play.getBoundingClientRect();if(rect.width<70||rect.top<0||rect.bottom>window.innerHeight||rect.left<0||rect.right>window.innerWidth||play.textContent.indexOf('PLAY')<0)throw new Error('Play button not visible');var keys=document.querySelectorAll('#keyboard .white-key').length;if(keys<10)throw new Error('Keyboard not built');document.getElementById('toggleKeys').click();if(!document.getElementById('keyboardDrawer').classList.contains('collapsed'))throw new Error('Keyboard toggle failed');document.getElementById('toggleKeys').click();console.log('SMOKE_UI_OK PLAY_VISIBLE '+Math.round(rect.width)+' KEYS '+keys);var ctx=new OfflineAudioContext(2,44100*2,44100);var bus=makeAudioGraph(ctx);scheduleNote(ctx,bus,{pitch:72,vel:.9},0.01,0.4);var b=await ctx.startRendering();var d=b.getChannelData(0);var sum=0;for(var i=0;i<d.length;i++)sum+=Math.abs(d[i]);var wav=wavBytes(b);var mp3=encodeMp3(b);if(wav.length<100||mp3.length<100)throw new Error('Export empty');document.querySelector('[data-tab=effects]').click();if(!document.getElementById('effectsView').classList.contains('active'))throw new Error('Effects tab failed');document.querySelector('[data-tab=roll]').click();console.log('SMOKE_EXPORT WAV_BYTES '+wav.length+' MP3_BYTES '+mp3.length);console.log('SMOKE_AUDIO_MEAN '+(sum/d.length).toFixed(6));}catch(e){console.error('SMOKE_AUDIO_FAIL '+e.message)}})()", null);
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


    /* Original Serum-rendered demonstration published at
       https://btesser.github.io/serum2vital/factory-leads/
       Fetched directly from its publisher on first run, cached privately.
       It is not redistributed inside this APK. */
    private void loadLeadReference() {
        new Thread(() -> {
            try {
                File cache = new File(getFilesDir(), "reference-c64-v1.mp3");
                byte[] audio;
                if (cache.exists() && cache.length() > 15000 && cache.length() < 2000000) {
                    audio = Files.readAllBytes(cache.toPath());
                } else {
                    URL url = new URL("https://raw.githubusercontent.com/btesser/serum2vital/gh-pages/factory-leads/LD%20C64%20Lead%20%5BAS%5D%20-%20serum.mp3");
                    HttpURLConnection conn = (HttpURLConnection)url.openConnection();
                    conn.setConnectTimeout(12000);
                    conn.setReadTimeout(18000);
                    conn.setRequestProperty("User-Agent","PulseStudio-C64-ResearchPlayer/1");
                    try {
                        if (conn.getResponseCode()!=200) throw new Exception("Reference HTTP " + conn.getResponseCode());
                        try(InputStream in=conn.getInputStream(); ByteArrayOutputStream out=new ByteArrayOutputStream()) {
                            byte[] b=new byte[8192];int n;
                            while((n=in.read(b))!=-1){out.write(b,0,n);if(out.size()>2000000)throw new Exception("Reference too large");}
                            audio=out.toByteArray();
                        }
                    } finally { conn.disconnect(); }
                    if(audio.length<15000)throw new Exception("Reference audio incomplete");
                    try(FileOutputStream fs=new FileOutputStream(cache)){fs.write(audio);}
                }
                String encoded=Base64.encodeToString(audio,Base64.NO_WRAP);
                Log.i(TAG,"REFERENCE_FETCH bytes="+audio.length);
                runOnUiThread(() -> {
                    if (webView!=null) webView.evaluateJavascript("window.PulseReference&&window.PulseReference.ready('"+encoded+"')",null);
                });
            }catch(Exception ex){
                Log.e(TAG,"REFERENCE_FETCH_FAILED "+ex.getMessage(),ex);
                String message=ex.getMessage()==null?"Network unavailable":ex.getMessage().replace("'","").replace("\\","/");
                runOnUiThread(()->{
                    if(webView!=null)webView.evaluateJavascript("window.PulseReference&&window.PulseReference.failed('"+message+"')",null);
                });
            }
        },"SerumC64AutoLoad").start();
    }
    private class Bridge {
        @JavascriptInterface public void prefetchLead() {loadLeadReference();}

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
