# Applies new native stereo and 7.1 DSP/UI without replacing the original FxSound engine.
from pathlib import Path

src = Path("source/spatial/Studio.cpp")
s = src.read_text(encoding="utf-8")
def replace_one(before, after):
    global s
    n = s.count(before)
    if n != 1:
        raise SystemExit(f"Expected one occurrence ({n}): {before[:100]!r}")
    s = s.replace(before, after)

replace_one('#include "AdvancedSpatial.h"', '#include "AdvancedSpatial.h"\n#include "AdvancedEffects.h"')
replace_one(' std::atomic<int> advancedSurround{1},diffuseVerb{1},reverbDamping{40};',
''' std::atomic<int> advancedSurround{1},diffuseVerb{1},reverbDamping{40};
 std::atomic<int> stereoChorus{0},stereoEcho{0},stereoPhaser{0};
 std::atomic<int> chorusWet{35},chorusRate{35},echoWet{35},echoDelay{280},echoFeedback{42};
 std::atomic<int> phaserWet{35},phaserRate{35},stereoWidth{100};
 std::atomic<int> orbitOn{0},orbitWet{35},orbitDelay{270},orbitFeedback{42},orbitSpeed{25};''')
replace_one('static advspatial::Engine enhancedSpatial;',
'''static advspatial::Engine enhancedSpatial;
static freshfx::StereoRack stereoRack;
static freshfx::SurroundOrbit orbitRack;''')
replace_one('spatial.reset();speakers.reset();corrections.reset();enhancedSpatial.reset();envelope=transient=0;',
            'spatial.reset();speakers.reset();corrections.reset();enhancedSpatial.reset();stereoRack.reset();orbitRack.reset();envelope=transient=0;')
replace_one('  float dry[256][8],wl[256]{},wr[256]{};bool useIR=false;',
'''  float dry[256][8],wl[256]{},wr[256]{};bool useIR=false;
  // Stereo DSP runs before 7.1 upmix, so both native stereo and 7.1 playback work.
  if(!compare&&(n==2||valid)){
   freshfx::StereoSettings st;
   st.chorus=cfg.stereoChorus!=0;st.echo=cfg.stereoEcho!=0;st.phaser=cfg.stereoPhaser!=0;
   st.chorusWet=cfg.chorusWet;st.chorusRate=cfg.chorusRate;
   st.echoWet=cfg.echoWet;st.echoDelay=cfg.echoDelay;st.echoFeedback=cfg.echoFeedback;
   st.phaserWet=cfg.phaserWet;st.phaserRate=cfg.phaserRate;st.width=cfg.stereoWidth;
   stereoRack.process(p,len,n,sr,st);
  }''')
replace_one('  }else spatial.reset();\n  for(int f=0;f<len;f++)for(int c=0;c<n;c++)',
'''  }else spatial.reset();
  if(valid&&!compare&&cfg.orbitOn){
   freshfx::OrbitSettings o;
   o.enabled=true;o.wet=cfg.orbitWet;o.delayMs=cfg.orbitDelay;
   o.feedback=cfg.orbitFeedback;o.speed=cfg.orbitSpeed;
   orbitRack.process(p,len,n,sr,mask,o);
  }
  for(int f=0;f<len;f++)for(int c=0;c<n;c++)''')
replace_one(' put("adaptive",cfg.advancedSurround);put("diffuse",cfg.diffuseVerb);put("damping",cfg.reverbDamping);',
''' put("adaptive",cfg.advancedSurround);put("diffuse",cfg.diffuseVerb);put("damping",cfg.reverbDamping);
 put("sChorus",cfg.stereoChorus);put("sEcho",cfg.stereoEcho);put("sPhaser",cfg.stereoPhaser);
 put("sChorusWet",cfg.chorusWet);put("sChorusRate",cfg.chorusRate);
 put("sEchoWet",cfg.echoWet);put("sEchoDelay",cfg.echoDelay);put("sEchoFeedback",cfg.echoFeedback);
 put("sPhaserWet",cfg.phaserWet);put("sPhaserRate",cfg.phaserRate);put("sWidth",cfg.stereoWidth);
 put("orbitOn",cfg.orbitOn);put("orbitWet",cfg.orbitWet);put("orbitDelay",cfg.orbitDelay);
 put("orbitFeedback",cfg.orbitFeedback);put("orbitSpeed",cfg.orbitSpeed);''')
replace_one('  get("adaptive",cfg.advancedSurround,1);get("diffuse",cfg.diffuseVerb,1);get("damping",cfg.reverbDamping,100);',
'''  get("adaptive",cfg.advancedSurround,1);get("diffuse",cfg.diffuseVerb,1);get("damping",cfg.reverbDamping,100);
  get("sChorus",cfg.stereoChorus,1);get("sEcho",cfg.stereoEcho,1);get("sPhaser",cfg.stereoPhaser,1);
  get("sChorusWet",cfg.chorusWet,100);get("sChorusRate",cfg.chorusRate,100);
  get("sEchoWet",cfg.echoWet,100);get("sEchoDelay",cfg.echoDelay,900);get("sEchoFeedback",cfg.echoFeedback,80);
  get("sPhaserWet",cfg.phaserWet,100);get("sPhaserRate",cfg.phaserRate,100);get("sWidth",cfg.stereoWidth,180);
  get("orbitOn",cfg.orbitOn,1);get("orbitWet",cfg.orbitWet,100);get("orbitDelay",cfg.orbitDelay,900);
  get("orbitFeedback",cfg.orbitFeedback,75);get("orbitSpeed",cfg.orbitSpeed,100);''')

stereo_page = r'''
// Stereo effects operate on channels L/R. For 7.1, the result feeds surround routing.
class StereoPage final:public Component {
 Label title,intro;
 ToggleButton chorus{"Stereo chorus / moving depth"},echo{"Ping-pong echoes (L / R)"},phaser{"Four-stage moving phaser"};
 Label labels[8];Slider sliders[8];TextButton reset{"Reset stereo FX"};
 std::atomic<int>* settings[8]={
  &cfg.chorusWet,&cfg.chorusRate,&cfg.echoWet,&cfg.echoDelay,
  &cfg.echoFeedback,&cfg.phaserWet,&cfg.phaserRate,&cfg.stereoWidth};
 const char* names[8]={
  "Chorus wet (%)","Chorus motion (0-100)","Echo wet (%)","Echo delay (ms)",
  "Echo feedback (%)","Phaser wet (%)","Phaser motion (0-100)","Stereo width (%)"};
 void sync(){
  chorus.setToggleState(cfg.stereoChorus!=0,dontSendNotification);
  echo.setToggleState(cfg.stereoEcho!=0,dontSendNotification);
  phaser.setToggleState(cfg.stereoPhaser!=0,dontSendNotification);
  for(int i=0;i<8;++i)sliders[i].setValue(settings[i]->load(),dontSendNotification);
 }
public:
 StereoPage(){
  addAndMakeVisible(title);addAndMakeVisible(intro);
  for(Component* p:std::initializer_list<Component*>{&chorus,&echo,&phaser,&reset})addAndMakeVisible(p);
  for(int i=0;i<8;++i){
   addAndMakeVisible(labels[i]);addAndMakeVisible(sliders[i]);
   label(labels[i],names[i]);auto& v=sliders[i];
   v.setRange(i==3?65:0,i==3?900:i==4?80:i==7?180:100,1);
   v.setTextBoxStyle(Slider::TextBoxRight,false,65,22);
   auto* setting=settings[i];auto* slider=&v;
   v.onValueChange=[setting,slider]{*setting=int(slider->getValue());};
   v.onDragEnd=[]{saveSettings();};
  }
  label(title,"STEREO FX  |  independent native effects");
  label(intro,"Processes the front L/R signal before 7.1 upmix. Each effect has a real-time DSP bypass. Effects are off until enabled.");
  chorus.onClick=[this]{cfg.stereoChorus=chorus.getToggleState();saveSettings();};
  echo.onClick=[this]{cfg.stereoEcho=echo.getToggleState();saveSettings();};
  phaser.onClick=[this]{cfg.stereoPhaser=phaser.getToggleState();saveSettings();};
  reset.onClick=[this]{
   cfg.stereoChorus=0;cfg.stereoEcho=0;cfg.stereoPhaser=0;
   cfg.chorusWet=35;cfg.chorusRate=35;cfg.echoWet=35;cfg.echoDelay=280;cfg.echoFeedback=42;
   cfg.phaserWet=35;cfg.phaserRate=35;cfg.stereoWidth=100;sync();saveSettings();
  };
  sync();
 }
 void resized()override{
  auto a=getLocalBounds().reduced(23);
  title.setBounds(a.removeFromTop(32));intro.setBounds(a.removeFromTop(43));
  auto row=[&](int i){auto r=a.removeFromTop(33);labels[i].setBounds(r.removeFromLeft(235));sliders[i].setBounds(r.removeFromLeft(385));};
  a.removeFromTop(6);chorus.setBounds(a.removeFromTop(34));row(0);row(1);
  a.removeFromTop(8);echo.setBounds(a.removeFromTop(34));row(2);row(3);row(4);
  a.removeFromTop(8);phaser.setBounds(a.removeFromTop(34));row(5);row(6);
  a.removeFromTop(8);row(7);a.removeFromTop(9);
  reset.setBounds(a.removeFromTop(35).removeFromLeft(200));
 }
};
'''
replace_one('class SpacePage final:public Component {', stereo_page+'\nclass SpacePage final:public Component {')
replace_one(' ToggleButton adaptive{"Adaptive stereo-to-7.1 extraction"};',
''' ToggleButton adaptive{"Adaptive stereo-to-7.1 extraction"};
 ToggleButton orbit{"Enable rotating 7.1 echo"};
 Label orbitTitle,orbitLabels[4];Slider orbitSliders[4];
 std::atomic<int>* orbitValues[4]={&cfg.orbitWet,&cfg.orbitDelay,&cfg.orbitFeedback,&cfg.orbitSpeed};''')
replace_one('  inverted.setToggleState(cfg.reverseSub,dontSendNotification);inverted.onClick=[this]{cfg.reverseSub=inverted.getToggleState();saveSettings();};',
'''  inverted.setToggleState(cfg.reverseSub,dontSendNotification);inverted.onClick=[this]{cfg.reverseSub=inverted.getToggleState();saveSettings();};
  addAndMakeVisible(orbit);addAndMakeVisible(orbitTitle);label(orbitTitle,"ORBIT ECHO  |  a delayed sound moves across six full-range speakers; sub remains untouched");
  const char* orbitNames[]={"Orbit echo wet (%)","Orbit delay (ms)","Orbit feedback (%)","Orbit speed (0-100)"};
  for(int i=0;i<4;++i){
   addAndMakeVisible(orbitLabels[i]);addAndMakeVisible(orbitSliders[i]);
   label(orbitLabels[i],orbitNames[i]);auto& slider=orbitSliders[i];
   slider.setRange(i==1?65:0,i==1?900:i==2?75:100,1);
   slider.setTextBoxStyle(Slider::TextBoxRight,false,65,22);
   slider.setValue(orbitValues[i]->load(),dontSendNotification);
   auto* value=orbitValues[i];auto* sliderRef=&slider;
   slider.onValueChange=[value,sliderRef]{*value=int(sliderRef->getValue());};
   slider.onDragEnd=[]{saveSettings();};
  }
  orbit.setToggleState(cfg.orbitOn!=0,dontSendNotification);
  orbit.onClick=[this]{cfg.orbitOn=orbit.getToggleState();saveSettings();};''')
replace_one('  r=a.removeFromTop(40);dampingLabel.setBounds(r.removeFromLeft(250));dampingSlider.setBounds(r.removeFromLeft(360));}',
'''  r=a.removeFromTop(40);dampingLabel.setBounds(r.removeFromLeft(250));dampingSlider.setBounds(r.removeFromLeft(360));
  a.removeFromTop(9);orbitTitle.setBounds(a.removeFromTop(28));
  orbit.setBounds(a.removeFromTop(32));
  for(int i=0;i<4;++i){r=a.removeFromTop(31);orbitLabels[i].setBounds(r.removeFromLeft(240));orbitSliders[i].setBounds(r.removeFromLeft(360));}
 }''')
replace_one('  tab("7.1 routing",new PageView(new room::Panel));tab("Spatial FX",new SpacePage);',
'''  tab("Stereo FX",new StereoPage);tab("7.1 FX",new SpacePage);
  tab("7.1 routing",new PageView(new room::Panel));''')
src.write_text(s,encoding="utf-8")
assert 'tab("Stereo FX",new StereoPage)' in s
assert 'orbitRack.process' in s and 'stereoRack.process' in s
print("Stereo and 7.1 effect controls + source DSP routing added.")
