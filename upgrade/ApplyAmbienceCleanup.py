# SPDX-License-Identifier: AGPL-3.0-or-later
# Replace moving/panning novelty FX with real hall reverb and wet-only speaker ambience.
from pathlib import Path

root=Path("source/spatial")
file=root/"Studio.cpp"
s=file.read_text(encoding="utf-8")
def once(a,b):
 global s
 n=s.count(a)
 if n!=1: raise RuntimeError(f"Expected one match, found {n}: {a[:115]!r}")
 s=s.replace(a,b)
def section(a,b,replace):
 global s
 start=s.index(a)
 end=s.index(b,start)
 s=s[:start]+replace+s[end:]

once('#include "AdvancedEffects.h"', '#include "AmbienceEffects.h"')
once('std::atomic<int> protect{0},bloom{0},cross{0},reverseSub{0},ir{0},attackSpread{0};',
     'std::atomic<int> protect{0},bloom{0},cross{0},reverseSub{0},ir{0};')
section(' std::atomic<int> stereoChorus{0}', ' std::atomic<bool> compare', ''' std::atomic<int> stereoChorus{0},stereoHall{0},stereoWet{35},stereoDecay{55},stereoDamp{45},stereoPre{25};
 std::atomic<int> chorusWet{23},chorusRate{28};
 std::atomic<int> surroundAmbient{0},surroundWet{35},surroundDecay{65},surroundDamp{50},surroundPre{30};
 std::atomic<int> ambientSL{100},ambientSR{100},ambientRL{100},ambientRR{100};
 std::atomic<uint32_t> mapping{0x76543210u};
''')
once(' Config(){for(auto& s:send)s=100;}', ' Config()=default;')
once('static freshfx::StereoRack stereoRack;\nstatic freshfx::SurroundOrbit orbitRack;',
     'static ambiencefx::DiffuseReverb stereoHallEngine,surroundAmbientEngine;\nstatic ambiencefx::SoftChorus stereoChorusEngine;')
once('static Filter extraNote;\n','')
once('enhancedSpatial.reset();stereoRack.reset();orbitRack.reset();',
     'enhancedSpatial.reset();stereoHallEngine.reset();surroundAmbientEngine.reset();stereoChorusEngine.reset();')
section(' int second=cfg.secondLevel.load()', ' uint32_t mapping=cfg.mapping.load();',
        '') 
section('  // Stereo DSP runs before 7.1 upmix', '  if(up){',
'''  // Ambient stereo rack. L/R stay in place: no orbit, ping-pong, or stereo-pan animation.
  if(!compare && (n==2||valid)){
   ambiencefx::ChorusSettings chorus;
   chorus.enabled=cfg.stereoChorus.load()!=0;
   chorus.wet=cfg.chorusWet.load();chorus.rate=cfg.chorusRate.load();
   stereoChorusEngine.process(p,len,n,sr,chorus);
   ambiencefx::ReverbSettings hall;
   hall.enabled=cfg.stereoHall.load()!=0;hall.wet=cfg.stereoWet.load();
   hall.decay=cfg.stereoDecay.load();hall.damping=cfg.stereoDamp.load();
   hall.preDelayMs=cfg.stereoPre.load();
   stereoHallEngine.process(p,len,n,sr,mask,hall,false);
  }
''')
once('   float amounts[8];for(int k=0;k<8;k++)amounts[k]=cfg.send[k]*.01f;\n','')
once('    if(second)out[dest]+=extraNote.run(mid,tuned)*second*.01f*gain;\n','')
once('    transient+=(std::abs(mid)-transient)*attackStep;\n','')
once('    if(cfg.attackSpread){float tail=mid*limit(1.f-(std::abs(mid)-transient)*12,0.f,1.f)*cfg.attackSpread*.004f*gain;out[4]+=tail;out[5]+=tail;}\n','')
once('    for(int k=0;k<8;k++)out[k]=dry[f][k]*gain+(out[k]-dry[f][k]*gain)*amounts[k];\n','')
once('   const float attackStep=1.f-std::exp(-75.f/sr),release=float(std::exp(-4./sr));',
     '   const float release=float(std::exp(-4./sr));')
section('  if(valid&&!compare&&cfg.orbitOn){', '  for(int f=0;f<len;f++)for(int c=0;c<n;c++)',
'''  // Ambience ONLY to side/rear channels. Works with true 7.1 even if upmix is off.
  // The front/centre/sub dry signals are untouched by this stage.
  if(valid&&!compare){
   ambiencefx::ReverbSettings ambience;
   ambience.enabled=cfg.surroundAmbient.load()!=0;
   ambience.wet=cfg.surroundWet.load();ambience.decay=cfg.surroundDecay.load();
   ambience.damping=cfg.surroundDamp.load();ambience.preDelayMs=cfg.surroundPre.load();
   ambience.sideLeft=cfg.ambientSL.load();ambience.sideRight=cfg.ambientSR.load();
   ambience.rearLeft=cfg.ambientRL.load();ambience.rearRight=cfg.ambientRR.load();
   surroundAmbientEngine.process(p,len,n,sr,mask,ambience,true);
  }
''')
section(' put("sChorus",cfg.stereoChorus)', ' x.setAttribute("mapping",',
''' put("sChorus",cfg.stereoChorus);put("sHall",cfg.stereoHall);put("sWet",cfg.stereoWet);
 put("sDecay",cfg.stereoDecay);put("sDamp",cfg.stereoDamp);put("sPre",cfg.stereoPre);
 put("sChorusWet",cfg.chorusWet);put("sChorusRate",cfg.chorusRate);
 put("ambOn",cfg.surroundAmbient);put("ambWet",cfg.surroundWet);
 put("ambDecay",cfg.surroundDecay);put("ambDamp",cfg.surroundDamp);put("ambPre",cfg.surroundPre);
 put("ambSL",cfg.ambientSL);put("ambSR",cfg.ambientSR);
 put("ambRL",cfg.ambientRL);put("ambRR",cfg.ambientRR);
 put("protect",cfg.protect);put("bloom",cfg.bloom);put("cross",cfg.cross);
 put("polarity",cfg.reverseSub);put("useIR",cfg.ir);
''')
once(' for(int k=0;k<8;k++){x.setAttribute("send"+String(k),cfg.send[k].load());x.setAttribute("offset"+String(k),roomstudio::controls().channel[k].offsetUs.load());}',
     ' for(int k=0;k<8;k++)x.setAttribute("offset"+String(k),roomstudio::controls().channel[k].offsetUs.load());')
section('  get("sChorus",cfg.stereoChorus', '  auto m=uint32_t(',
'''  get("sChorus",cfg.stereoChorus,1);get("sHall",cfg.stereoHall,1);get("sWet",cfg.stereoWet,100);
  get("sDecay",cfg.stereoDecay,100);get("sDamp",cfg.stereoDamp,100);get("sPre",cfg.stereoPre,120);
  get("sChorusWet",cfg.chorusWet,100);get("sChorusRate",cfg.chorusRate,100);
  get("ambOn",cfg.surroundAmbient,1);get("ambWet",cfg.surroundWet,100);
  get("ambDecay",cfg.surroundDecay,100);get("ambDamp",cfg.surroundDamp,100);get("ambPre",cfg.surroundPre,120);
  get("ambSL",cfg.ambientSL,150);get("ambSR",cfg.ambientSR,150);
  get("ambRL",cfg.ambientRL,150);get("ambRR",cfg.ambientRR,150);
  get("protect",cfg.protect,1);get("bloom",cfg.bloom,100);get("cross",cfg.cross,200);
  get("polarity",cfg.reverseSub,1);get("useIR",cfg.ir,1);
''')
once('   cfg.send[k]=jlimit(0,150,x->getIntAttribute("send"+String(k),100));\n','')

stereoPage=r'''
class StereoPage final:public Component {
 Label title,help,labels[6];
 ToggleButton hall{"Stereo hall reverb"},chorus{"Soft chorus / depth (no panning)"};
 Slider values[6];TextButton reset{"Reset stereo effects"};
 std::atomic<int>* targets[6]={&cfg.stereoWet,&cfg.stereoDecay,&cfg.stereoDamp,&cfg.stereoPre,&cfg.chorusWet,&cfg.chorusRate};
 const char* captions[6]={"Hall wet level (%)","Hall decay (short to long)","Hall high-frequency damping (%)",
 "Pre-delay (ms)","Chorus mix (%)","Chorus speed"};
 void reload(){
  hall.setToggleState(cfg.stereoHall!=0,dontSendNotification);
  chorus.setToggleState(cfg.stereoChorus!=0,dontSendNotification);
  for(int i=0;i<6;++i)values[i].setValue(targets[i]->load(),dontSendNotification);
 }
public:
 StereoPage(){
  for(Component* p:std::initializer_list<Component*>{&title,&help,&hall,&chorus,&reset})addAndMakeVisible(p);
  label(title,"STEREO AMBIENCE  |  room depth without moving the soundstage");
  label(help,"Reverb and gentle chorus on front L/R. 7.1 processing uses these front channels as its source.");
  for(int i=0;i<6;++i){
   addAndMakeVisible(labels[i]);addAndMakeVisible(values[i]);label(labels[i],captions[i]);
   auto& slider=values[i];slider.setRange(0,i==3?120:100,1);
   slider.setTextBoxStyle(Slider::TextBoxRight,false,56,22);
   auto* target=targets[i],*dummy=targets[i];(void)dummy;
   auto* control=&slider;
   slider.onValueChange=[target,control]{*target=int(control->getValue());};
   slider.onDragEnd=[]{saveSettings();};
  }
  hall.onClick=[this]{cfg.stereoHall=hall.getToggleState();saveSettings();};
  chorus.onClick=[this]{cfg.stereoChorus=chorus.getToggleState();saveSettings();};
  reset.onClick=[this]{
   cfg.stereoHall=0;cfg.stereoWet=35;cfg.stereoDecay=55;cfg.stereoDamp=45;cfg.stereoPre=25;
   cfg.stereoChorus=0;cfg.chorusWet=23;cfg.chorusRate=28;
   reload();saveSettings();
  };
  reload();
 }
 void resized()override{
  auto area=getLocalBounds().reduced(24);
  title.setBounds(area.removeFromTop(34));help.setBounds(area.removeFromTop(42));
  hall.setBounds(area.removeFromTop(35));
  for(int i=0;i<6;++i){
   if(i==4){area.removeFromTop(13);chorus.setBounds(area.removeFromTop(37));}
   auto row=area.removeFromTop(36);
   labels[i].setBounds(row.removeFromLeft(265));
   values[i].setBounds(row.removeFromLeft(370));
  }
  area.removeFromTop(16);reset.setBounds(area.removeFromTop(36).removeFromLeft(225));
 }
};
'''

surroundPage=r'''
class SpacePage final:public Component {
 Label title,help,heading,labels[10],legacyTitle,algorithmTitle,fileInfo,bassNote;
 Slider values[10],bass;ComboBox algorithm;
 ToggleButton ambient{"Enable 7.1 ambience-only reverb"},subInvert{"Invert subwoofer polarity"};
 TextButton wav{"Load room impulse WAV"},reset{"Reset surround ambience"};
 std::atomic<int>* target[10]={
  &cfg.surroundWet,&cfg.surroundDecay,&cfg.surroundDamp,&cfg.surroundPre,
  &cfg.ambientSL,&cfg.ambientSR,&cfg.ambientRL,&cfg.ambientRR,
  &cfg.bloom,&cfg.reverbDamping};
 const char* captions[10]={
  "Surround ambience wet (%)","Surround decay (short to long)",
  "High-frequency damping (%)","Pre-delay (ms)",
  "Side LEFT wet send (%)","Side RIGHT wet send (%)",
  "Rear LEFT wet send (%)","Rear RIGHT wet send (%)",
  "Original room ducking (%)","Original FDN damping (%)"};
 void refresh(){
  ambient.setToggleState(cfg.surroundAmbient!=0,dontSendNotification);
  for(int i=0;i<10;++i)values[i].setValue(target[i]->load(),dontSendNotification);
 }
public:
 SpacePage(){
  for(Component* p:std::initializer_list<Component*>{&title,&help,&heading,&legacyTitle,&algorithmTitle,
  &fileInfo,&bassNote,&algorithm,&ambient,&subInvert,&wav,&reset,&bass})addAndMakeVisible(p);
  label(title,"7.1 AMBIENCE  |  send the room, not the dry sound");
  label(help,"A separate diffuse reverb feeds sides and rears only; front, centre and sub are untouched. Requires Windows 7.1 output.");
  label(heading,"AMBIENCE OUTPUTS  |  individual wet sends; 0 = silent, 100 = full");
  label(legacyTitle,"OPTIONAL ORIGINAL ROOM PROCESSING");
  label(algorithmTitle,"Legacy room / convolution");
  label(bassNote,"Bass crossover (Hz; zero = off)");
  for(int i=0;i<10;++i){
   addAndMakeVisible(labels[i]);addAndMakeVisible(values[i]);
   label(labels[i],captions[i]);auto& slider=values[i];
   slider.setRange(0,i==3?120:(i>=4&&i<=7)?150:100,1);
   slider.setTextBoxStyle(Slider::TextBoxRight,false,54,22);
   auto* v=target[i];auto* control=&slider;
   slider.onValueChange=[v,control]{*v=int(control->getValue());};
   slider.onDragEnd=[]{saveSettings();};
  }
  ambient.onClick=[this]{cfg.surroundAmbient=ambient.getToggleState();saveSettings();};
  algorithm.addItem("Original feedback room",1);
  algorithm.addItem("Diffuse 8-line FDN room",2);
  algorithm.addItem("Room impulse convolution (WAV)",3);
  algorithm.setSelectedId(cfg.ir?3:(cfg.diffuseVerb?2:1),dontSendNotification);
  algorithm.onChange=[this]{
   if(algorithm.getSelectedId()==3 && cfg.irPath.isEmpty()){
    label(fileInfo,"Load a room WAV first.");
    algorithm.setSelectedId(2,dontSendNotification);
   }
   cfg.ir=(algorithm.getSelectedId()==3);
   cfg.diffuseVerb=(algorithm.getSelectedId()==2);
   saveSettings();
  };
  label(fileInfo,cfg.irPath.isEmpty()?"No room WAV selected":File(cfg.irPath).getFileName());
  wav.onClick=[this]{
   FileChooser chooser("Select room impulse response",{},"*.wav");
   if(chooser.browseForFileToOpen()){
    int sampleRate=room::controls().rate;String error=loadIR(chooser.getResult(),sampleRate>=22050?sampleRate:48000);
    if(error.isEmpty()){
     cfg.ir=1;cfg.diffuseVerb=0;algorithm.setSelectedId(3,dontSendNotification);
     label(fileInfo,chooser.getResult().getFileName());saveSettings();
    }else label(fileInfo,error);
   }
  };
  bass.setRange(0,200,1);bass.setTextBoxStyle(Slider::TextBoxRight,false,56,22);
  bass.setValue(cfg.cross,dontSendNotification);
  bass.onValueChange=[this]{int v=int(bass.getValue());cfg.cross=v<30?0:v;};
  bass.onDragEnd=[this]{bass.setValue(cfg.cross,dontSendNotification);saveSettings();};
  subInvert.setToggleState(cfg.reverseSub,dontSendNotification);
  subInvert.onClick=[this]{cfg.reverseSub=subInvert.getToggleState();saveSettings();};
  reset.onClick=[this]{
   cfg.surroundAmbient=0;cfg.surroundWet=35;cfg.surroundDecay=65;cfg.surroundDamp=50;cfg.surroundPre=30;
   cfg.ambientSL=100;cfg.ambientSR=100;cfg.ambientRL=100;cfg.ambientRR=100;
   refresh();saveSettings();
  };
  refresh();
 }
 void resized()override{
  auto a=getLocalBounds().reduced(17,9);
  title.setBounds(a.removeFromTop(28));help.setBounds(a.removeFromTop(37));
  ambient.setBounds(a.removeFromTop(30));
  auto row=[&](int i,int width=230){
   auto r=a.removeFromTop(27);
   labels[i].setBounds(r.removeFromLeft(width));
   values[i].setBounds(r.removeFromLeft(340));
  };
  for(int i=0;i<4;++i)row(i);
  a.removeFromTop(7);heading.setBounds(a.removeFromTop(29));
  for(int i=4;i<8;++i)row(i);
  a.removeFromTop(9);reset.setBounds(a.removeFromTop(31).removeFromLeft(185));
  a.removeFromTop(9);legacyTitle.setBounds(a.removeFromTop(29));
  auto r=a.removeFromTop(29);algorithmTitle.setBounds(r.removeFromLeft(200));
  algorithm.setBounds(r.removeFromLeft(223));wav.setBounds(r.removeFromLeft(175));fileInfo.setBounds(r);
  row(8);row(9);
  r=a.removeFromTop(31);bassNote.setBounds(r.removeFromLeft(230));
  bass.setBounds(r.removeFromLeft(220));subInvert.setBounds(r);
 }
};
'''
section('class StereoPage final:public Component {', 'class SpacePage final:public Component {', stereoPage+"\n")
section('class SpacePage final:public Component {', '// The correction page controls actual DSP modules',surroundPage+"\n")
once('tab("Stereo FX",new StereoPage);tab("7.1 FX",new SpacePage);',
     'tab("Stereo ambience",new StereoPage);tab("7.1 ambience",new PageView(new SpacePage));')
file.write_text(s,encoding="utf-8")

# Disable the older non-ambient tuned-note and high-frequency sends, including
# previously persisted settings. Keep the room engine ABI for the old tests/driver.
roomPanel=root/"RoomPanel.h"
r=roomPanel.read_text(encoding="utf-8")
r=r.replace('class Panel final:public Component, private Timer {',
'''class Panel final:public Component, private Timer {
 static bool visibleParameter(int i){return i==center||i==sub||i==sides||i==roomMix||i==decay||i==output;}
''')
r=r.replace('  for(int i=1;i<count;++i){','  for(int i=1;i<count;++i){if(!visibleParameter(i))continue;')
r=r.replace('for(int i=1;i<count;i++){if(choice(i))', 'for(int i=1;i<count;i++){if(!visibleParameter(i))continue;if(choice(i))')
r=r.replace('for(int i=1;i<count;++i){auto row=area.removeFromTop(29);',
            'for(int i=1;i<count;++i){if(!visibleParameter(i))continue;auto row=area.removeFromTop(34);')
r=r.replace('inline void restore(){if(auto xml=XmlDocument::parse(stateFile()))for(int i=0;i<count;++i)\n controls().value[i]=jlimit(spec[i].lo,spec[i].hi,xml->getIntAttribute("p"+String(i>=note?i+2:i),spec[i].initial));}',
'''inline void restore(){if(auto xml=XmlDocument::parse(stateFile()))for(int i=0;i<count;++i)
 controls().value[i]=jlimit(spec[i].lo,spec[i].hi,xml->getIntAttribute("p"+String(i>=note?i+2:i),spec[i].initial));
 controls().value[noteGain]=0;controls().value[bandGain]=0;}''')
roomPanel.write_text(r,encoding="utf-8")
roomEngine=root/"RoomEngine.h"
h=roomEngine.read_text(encoding="utf-8")
h=h.replace('{"Tuned note send",0,100,30}', '{"Tuned note send",0,100,0}')
h=h.replace('{"High-frequency send",0,100,28}', '{"High-frequency send",0,100,0}')
roomEngine.write_text(h,encoding="utf-8")

# Remove the old abandoned orbit/ping-pong algorithms from built project sources.
for dead in ("AdvancedEffects.h","AdvancedEffectsTest.cpp"):
 p=root/dead
 if p.exists():p.unlink()

assert 'orbitRack' not in s and 'ping-pong' not in s.lower()
assert 'class StereoPage' in s and 'class SpacePage' in s
assert 'surroundAmbientEngine.process' in s and 'stereoHallEngine.process' in s
assert 'visibleParameter' in r
print("Purged moving/panning effects and tuned sends; wired wet-only stereo and surround ambience.")
