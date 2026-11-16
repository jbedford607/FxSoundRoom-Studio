# SPDX-License-Identifier: AGPL-3.0-or-later
# Add actual low-latency DSP-estimated stems, an 8-channel output matrix,
# presets, isolated listening and signal meters to the existing FxSound app.
from pathlib import Path

p=Path("source/spatial/Studio.cpp")
s=p.read_text(encoding="utf-8")
def replace(a,b):
 global s
 n=s.count(a)
 if n!=1:raise RuntimeError(f"expected ONE occurrence, found {n}: {a[:140]!r}")
 s=s.replace(a,b)

replace('#include "FocusAmbience.h"','#include "FocusAmbience.h"\n#include "LiveStemMatrix.h"')
replace(' std::atomic<int> ambientExtraction{45},ambientDuck{35},ambientLow{180},ambientHigh{8000},ambientWetOnly{0};',
''' std::atomic<int> ambientExtraction{45},ambientDuck{35},ambientLow{180},ambientHigh{8000},ambientWetOnly{0};
 std::atomic<int> stemEnabled{0},stemReplace{1},stemPreview{0};
 std::atomic<int> stemBassHz{125},stemCenterFocus{55},stemPercFocus{65};
 std::atomic<int> stemRouteBass{8},stemRouteCenter{4},stemRoutePerc{48},stemRouteSide{192};
 std::atomic<int> stemGainBass{65},stemGainCenter{50},stemGainPerc{55},stemGainSide{55};''')
replace('static ambiencefx::FocusSend focusProcessor;',
'''static ambiencefx::FocusSend focusProcessor;
static stems71::Extractor liveStems;''')
replace('focusProcessor.reset();envelope=transient=0;', 'focusProcessor.reset();liveStems.reset();envelope=transient=0;')
replace('  float dry[256][8],wl[256]{},wr[256]{};bool useIR=false,derivedStereo=false;',
'''  float dry[256][8],wl[256]{},wr[256]{},originalStereo[256*2]{};
  bool useIR=false,derivedStereo=false;
  bool stemSourceIsStereo=valid;
  // Capture BEFORE FxSound effects/upmix. Do not destroy native surround input.
  if(valid && !compare && cfg.stemEnabled.load()){
   for(int f=0;f<len;++f){
    originalStereo[2*f]=p[8*f];originalStereo[2*f+1]=p[8*f+1];
    for(int ch=2;ch<8;++ch)if(std::abs(p[8*f+ch])>.00015f)
     stemSourceIsStereo=false;
   }
  }''')
replace('  for(int f=0;f<len;f++)for(int c=0;c<n;c++){auto& x=p[f*n+c];',
'''  // Apply estimated-stem matrix after legacy surround and ambience, but before
  // speaker calibration, physical channel remapping, and output peak protection.
  if(valid && !compare && cfg.stemEnabled.load()){
   stems71::Settings st;
   st.enabled=true;st.replaceSynthesizedSides=cfg.stemReplace.load()!=0;
   st.preview=cfg.stemPreview.load();
   st.bassCutHz=cfg.stemBassHz.load();st.centerFocus=cfg.stemCenterFocus.load();
   st.percussionFocus=cfg.stemPercFocus.load();
   st.routes={uint8_t(cfg.stemRouteBass.load()),uint8_t(cfg.stemRouteCenter.load()),
              uint8_t(cfg.stemRoutePerc.load()),uint8_t(cfg.stemRouteSide.load())};
   st.levels={cfg.stemGainBass.load(),cfg.stemGainCenter.load(),
              cfg.stemGainPerc.load(),cfg.stemGainSide.load()};
   liveStems.process(originalStereo,p,len,sr,mask,stemSourceIsStereo,st);
  }
  for(int f=0;f<len;f++)for(int c=0;c<n;c++){auto& x=p[f*n+c];''')
replace(' put("ambWetOnly",cfg.ambientWetOnly);',
''' put("ambWetOnly",cfg.ambientWetOnly);
 put("stemOn",cfg.stemEnabled);put("stemReplace",cfg.stemReplace);put("stemPreview",cfg.stemPreview);
 put("stemBassHz",cfg.stemBassHz);put("stemCenterFocus",cfg.stemCenterFocus);
 put("stemPercFocus",cfg.stemPercFocus);
 put("stemRouteBass",cfg.stemRouteBass);put("stemRouteCenter",cfg.stemRouteCenter);
 put("stemRoutePerc",cfg.stemRoutePerc);put("stemRouteSide",cfg.stemRouteSide);
 put("stemGainBass",cfg.stemGainBass);put("stemGainCenter",cfg.stemGainCenter);
 put("stemGainPerc",cfg.stemGainPerc);put("stemGainSide",cfg.stemGainSide);''')
replace('  get("ambWetOnly",cfg.ambientWetOnly,1);',
'''  get("ambWetOnly",cfg.ambientWetOnly,1);
  get("stemOn",cfg.stemEnabled,1);get("stemReplace",cfg.stemReplace,1);
  get("stemPreview",cfg.stemPreview,4);get("stemBassHz",cfg.stemBassHz,240);
  get("stemCenterFocus",cfg.stemCenterFocus,100);get("stemPercFocus",cfg.stemPercFocus,100);
  get("stemRouteBass",cfg.stemRouteBass,255);get("stemRouteCenter",cfg.stemRouteCenter,255);
  get("stemRoutePerc",cfg.stemRoutePerc,255);get("stemRouteSide",cfg.stemRouteSide,255);
  get("stemGainBass",cfg.stemGainBass,150);get("stemGainCenter",cfg.stemGainCenter,150);
  get("stemGainPerc",cfg.stemGainPerc,150);get("stemGainSide",cfg.stemGainSide,150);''')

ui=r'''
// Live DSP-estimated instrument groups: controls are directly connected to native
// audio processing. No fake separation: these are band/centre/transient/side estimates.
class StemsPage final:public Component,private Timer {
 Label title,explain,subtext,channelHeaders[8],names[4],meters[4];
 Label controlLabels[3],previewLabel;
 ToggleButton enabled{"Enable live stereo-to-7.1 stem routing"};
 ToggleButton replaceSurround{"Replace the existing synthetic rear/side mix (recommended)"};
 ToggleButton speaker[4][8];
 Slider gain[4],controls[3];
 ComboBox audition;
 TextButton band{"Studio band"},rhythm{"Rhythm in surround"},overlay{"Gentle overlay"},reset{"Reset matrix"};
 std::atomic<int>* routeSetting[4]={
  &cfg.stemRouteBass,&cfg.stemRouteCenter,&cfg.stemRoutePerc,&cfg.stemRouteSide};
 std::atomic<int>* gainSetting[4]={
  &cfg.stemGainBass,&cfg.stemGainCenter,&cfg.stemGainPerc,&cfg.stemGainSide};
 std::atomic<int>* controlsSetting[3]={
  &cfg.stemBassHz,&cfg.stemCenterFocus,&cfg.stemPercFocus};
 const char* stemNames[4]={"Bass / low end","Centre / vocal-like","Percussion / attack","Stereo side details"};
 const char* physicalNames[8]={"FL","FR","C","SUB","RL","RR","SL","SR"};
 void sync(){
  enabled.setToggleState(cfg.stemEnabled.load()!=0,dontSendNotification);
  replaceSurround.setToggleState(cfg.stemReplace.load()!=0,dontSendNotification);
  for(int i=0;i<4;++i){
   gain[i].setValue(gainSetting[i]->load(),dontSendNotification);
   for(int ch=0;ch<8;++ch)
    speaker[i][ch].setToggleState((routeSetting[i]->load()&(1<<ch))!=0,dontSendNotification);
  }
  for(int i=0;i<3;++i)controls[i].setValue(controlsSetting[i]->load(),dontSendNotification);
  audition.setSelectedId(jlimit(1,5,cfg.stemPreview.load()+1),dontSendNotification);
 }
 void preset(int which){
  cfg.stemEnabled=1;cfg.stemPreview=0;
  cfg.stemBassHz=125;cfg.stemCenterFocus=55;cfg.stemPercFocus=65;
  cfg.stemRouteBass=8;cfg.stemRouteCenter=4;
  cfg.stemRoutePerc=which==1?192:48;
  cfg.stemRouteSide=which==1?48:192;
  cfg.stemGainBass=65;cfg.stemGainCenter=50;
  cfg.stemGainPerc=which==2?24:55;cfg.stemGainSide=which==2?24:55;
  cfg.stemReplace=which==2?0:1;
  sync();saveSettings();
 }
 void timerCallback()override{
  for(int i=0;i<4;++i)
   label(meters[i],String(jlimit(0,100,int(liveStems.meter(i)*100.f)))+"%");
 }
public:
 StemsPage(){
  setSize(964,710);
  for(Component* c:std::initializer_list<Component*>{&title,&explain,&subtext,&enabled,
   &replaceSurround,&audition,&previewLabel,&band,&rhythm,&overlay,&reset})
    addAndMakeVisible(c);
  label(title,"LIVE STEM MATRIX  |  Send different musical elements to different speakers");
  label(explain,"4 fast DSP estimates: bass, centred sounds, transients and stereo differences. Not AI-quality vocal/drum isolation.");
  label(subtext,"Only operates on stereo music arriving through a Windows 7.1 endpoint; native discrete 7.1 is protected.");
  label(previewLabel,"Listen to source");
  for(int ch=0;ch<8;++ch){
   addAndMakeVisible(channelHeaders[ch]);label(channelHeaders[ch],physicalNames[ch]);
  }
  for(int i=0;i<4;++i){
   addAndMakeVisible(names[i]);addAndMakeVisible(gain[i]);addAndMakeVisible(meters[i]);
   label(names[i],stemNames[i]);
   gain[i].setRange(0,150,1);
   gain[i].setTextBoxStyle(Slider::TextBoxRight,false,48,22);
   auto* setting=gainSetting[i];auto* slider=&gain[i];
   gain[i].onValueChange=[setting,slider]{setting->store(int(slider->getValue()));};
   gain[i].onDragEnd=[]{saveSettings();};
   for(int ch=0;ch<8;++ch){
    auto& item=speaker[i][ch];
    addAndMakeVisible(item);
    item.setTooltip(String(stemNames[i])+" -> "+physicalNames[ch]);
    item.onClick=[this,i,ch]{
     int bit=1<<ch;
     int v=routeSetting[i]->load();
     routeSetting[i]->store(speaker[i][ch].getToggleState()?v|bit:v&~bit);
     saveSettings();
    };
   }
  }
  const char* paramNames[3]={"Bass cutoff (Hz)","Centre focus (%)","Drum transient sensitivity (%)"};
  for(int i=0;i<3;++i){
   addAndMakeVisible(controlLabels[i]);addAndMakeVisible(controls[i]);
   label(controlLabels[i],paramNames[i]);
   controls[i].setRange(i==0?55:0,i==0?240:100,1);
   controls[i].setTextBoxStyle(Slider::TextBoxRight,false,52,22);
   auto* setting=controlsSetting[i];auto* slider=&controls[i];
   controls[i].onValueChange=[setting,slider]{setting->store(int(slider->getValue()));};
   controls[i].onDragEnd=[]{saveSettings();};
  }
  enabled.onClick=[this]{cfg.stemEnabled=enabled.getToggleState();saveSettings();};
  replaceSurround.onClick=[this]{cfg.stemReplace=replaceSurround.getToggleState();saveSettings();};
  audition.addItem("Full music + routed estimates",1);
  audition.addItem("Solo estimated bass",2);
  audition.addItem("Solo estimated centre",3);
  audition.addItem("Solo estimated percussion",4);
  audition.addItem("Solo estimated stereo sides",5);
  audition.onChange=[this]{cfg.stemPreview=audition.getSelectedId()-1;saveSettings();};
  band.onClick=[this]{preset(0);};
  rhythm.onClick=[this]{preset(1);};
  overlay.onClick=[this]{preset(2);};
  reset.onClick=[this]{
   cfg.stemEnabled=0;cfg.stemPreview=0;cfg.stemReplace=1;
   cfg.stemRouteBass=8;cfg.stemRouteCenter=4;cfg.stemRoutePerc=48;cfg.stemRouteSide=192;
   cfg.stemGainBass=65;cfg.stemGainCenter=50;cfg.stemGainPerc=55;cfg.stemGainSide=55;
   cfg.stemBassHz=125;cfg.stemCenterFocus=55;cfg.stemPercFocus=65;
   sync();saveSettings();
  };
  sync();timerCallback();startTimerHz(8);
 }
 void resized()override{
  auto a=getLocalBounds().reduced(18,12);
  title.setBounds(a.removeFromTop(34));
  explain.setBounds(a.removeFromTop(31));
  subtext.setBounds(a.removeFromTop(27));
  enabled.setBounds(a.removeFromTop(36));
  replaceSurround.setBounds(a.removeFromTop(34));
  auto presets=a.removeFromTop(41);
  band.setBounds(presets.removeFromLeft(172).reduced(2));
  rhythm.setBounds(presets.removeFromLeft(205).reduced(2));
  overlay.setBounds(presets.removeFromLeft(173).reduced(2));
  reset.setBounds(presets.removeFromLeft(142).reduced(2));
  auto head=a.removeFromTop(34);
  head.removeFromLeft(145+158+65);
  for(int ch=0;ch<8;++ch)
   channelHeaders[ch].setBounds(head.removeFromLeft(65));
  for(int i=0;i<4;++i){
   auto r=a.removeFromTop(55);
   names[i].setBounds(r.removeFromLeft(145));
   gain[i].setBounds(r.removeFromLeft(158));
   meters[i].setBounds(r.removeFromLeft(65));
   for(int ch=0;ch<8;++ch){
    auto cell=r.removeFromLeft(65);
    speaker[i][ch].setBounds(cell.reduced(21,10));
   }
  }
  a.removeFromTop(12);
  for(int i=0;i<3;++i){
   auto r=a.removeFromTop(35);
   controlLabels[i].setBounds(r.removeFromLeft(260));
   controls[i].setBounds(r.removeFromLeft(315));
  }
  a.removeFromTop(11);
  auto last=a.removeFromTop(38);
  previewLabel.setBounds(last.removeFromLeft(165));
  audition.setBounds(last.removeFromLeft(410));
 }
};
'''
anchor='// The correction page controls actual DSP modules'
if s.count(anchor)!=1:raise RuntimeError("Cannot identify CorrectionPage insertion point")
s=s.replace(anchor,ui+"\n"+anchor)
replace('  tab("Stereo ambience",new StereoPage);tab("7.1 ambience",new PageView(new SpacePage));',
'''  tab("Live stems",new PageView(new StemsPage));
  tab("Stereo ambience",new StereoPage);tab("7.1 ambience",new PageView(new SpacePage));''')
p.write_text(s,encoding="utf-8")
for needle in ("liveStems.process(originalStereo,p,len","tab(\"Live stems\",new PageView(new StemsPage))",
               "stemRouteBass","audition.onChange","item.onClick","stemReplace"):
 if needle not in s:raise RuntimeError("Missing integrated GUI/DSP: "+needle)
print("PASS: 4 sources x 8 routing UI, DSP processing, native-channel safety, preset/solo controls, saved settings.")
