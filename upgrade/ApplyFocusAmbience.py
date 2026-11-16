# SPDX-License-Identifier: AGPL-3.0-or-later
# Applied after ApplyAmbienceCleanup.py to the original FxSound source.
from pathlib import Path

p=Path("source/spatial/Studio.cpp")
s=p.read_text(encoding="utf-8")
def change(old,new):
 global s
 n=s.count(old)
 if n!=1: raise RuntimeError(f"Expected one replacement, got {n}: {old[:120]!r}")
 s=s.replace(old,new)

change('#include "AmbienceEffects.h"','#include "AmbienceEffects.h"\n#include "FocusAmbience.h"')
change(' std::atomic<int> ambientSL{100},ambientSR{100},ambientRL{100},ambientRR{100};',
''' std::atomic<int> ambientSL{100},ambientSR{100},ambientRL{100},ambientRR{100};
 std::atomic<int> ambientExtraction{45},ambientDuck{35},ambientLow{180},ambientHigh{8000},ambientWetOnly{0};''')
change('static ambiencefx::SoftChorus stereoChorusEngine;',
       'static ambiencefx::SoftChorus stereoChorusEngine;\nstatic ambiencefx::FocusSend focusProcessor;')
change('surroundAmbientEngine.reset();stereoChorusEngine.reset();',
       'surroundAmbientEngine.reset();stereoChorusEngine.reset();focusProcessor.reset();')
change('  float dry[256][8],wl[256]{},wr[256]{};bool useIR=false;',
       '  float dry[256][8],wl[256]{},wr[256]{};bool useIR=false,derivedStereo=false;')
change('   for(int f=0;f<len;f++){std::copy_n(p+f*8,8,dry[f]);wl[f]=dry[f][0];wr[f]=dry[f][1];}',
'''   derivedStereo=true;
   for(int f=0;f<len;f++){
    std::copy_n(p+f*8,8,dry[f]);wl[f]=dry[f][0];wr[f]=dry[f][1];
    if(std::abs(dry[f][4])+std::abs(dry[f][5])+std::abs(dry[f][6])+std::abs(dry[f][7])>1.e-6f)
     derivedStereo=false;
   }''')
change('   surroundAmbientEngine.process(p,len,n,sr,mask,ambience,true);',
'''   ambiencefx::FocusSettings focus;
   focus.extraction=cfg.ambientExtraction.load();focus.duckPercent=cfg.ambientDuck.load();
   focus.lowCutHz=cfg.ambientLow.load();focus.highCutHz=cfg.ambientHigh.load();
   focus.wetOnly=cfg.ambientWetOnly.load()!=0;
   focusProcessor.process(p,len,n,sr,mask,ambience,focus,surroundAmbientEngine,derivedStereo);''')
change(' put("ambRL",cfg.ambientRL);put("ambRR",cfg.ambientRR);',
''' put("ambRL",cfg.ambientRL);put("ambRR",cfg.ambientRR);
 put("ambExtract",cfg.ambientExtraction);put("ambDuck",cfg.ambientDuck);
 put("ambLow",cfg.ambientLow);put("ambHigh",cfg.ambientHigh);
 put("ambWetOnly",cfg.ambientWetOnly);''')
change('  get("ambRL",cfg.ambientRL,150);get("ambRR",cfg.ambientRR,150);',
'''  get("ambRL",cfg.ambientRL,150);get("ambRR",cfg.ambientRR,150);
  get("ambExtract",cfg.ambientExtraction,100);get("ambDuck",cfg.ambientDuck,100);
  get("ambLow",cfg.ambientLow,4000);get("ambHigh",cfg.ambientHigh,18000);
  get("ambWetOnly",cfg.ambientWetOnly,1);''')
change('Label title,help,heading,labels[10],legacyTitle,algorithmTitle,fileInfo,bassNote;',
       'Label title,help,heading,focusTitle,labels[14],legacyTitle,algorithmTitle,fileInfo,bassNote;')
change(' Slider values[10],bass;ComboBox algorithm;',
       ' Slider values[14],bass;ComboBox algorithm;')
change(' ToggleButton ambient{"Enable 7.1 ambience-only reverb"},subInvert{"Invert subwoofer polarity"};',
       ''' ToggleButton ambient{"Enable 7.1 ambience-only reverb"},subInvert{"Invert subwoofer polarity"};
 ToggleButton wetOnly{"Wet-only sides / rears for stereo upmix (preserve native 7.1)"};''')
change(' std::atomic<int>* target[10]={', ' std::atomic<int>* target[14]={')
change('  &cfg.bloom,&cfg.reverbDamping};',
       '  &cfg.bloom,&cfg.reverbDamping,&cfg.ambientExtraction,&cfg.ambientDuck,&cfg.ambientLow,&cfg.ambientHigh};')
change(' const char* captions[10]={',' const char* captions[14]={')
change('  "Original room ducking (%)","Original FDN damping (%)"};',
'''  "Original room ducking (%)","Original FDN damping (%)",
  "Stereo difference extraction (%)","Wet reverb ducking (%)",
  "Ambience low cut (Hz)","Ambience high cut (Hz)"};''')
change('  for(int i=0;i<10;++i)values[i].setValue(target[i]->load(),dontSendNotification);',
'''  wetOnly.setToggleState(cfg.ambientWetOnly!=0,dontSendNotification);
  for(int i=0;i<14;++i)values[i].setValue(target[i]->load(),dontSendNotification);''')
change('&fileInfo,&bassNote,&algorithm,&ambient,&subInvert,&wav,&reset,&bass',
       '&fileInfo,&bassNote,&algorithm,&ambient,&subInvert,&wav,&reset,&bass,&focusTitle,&wetOnly')
change('  label(heading,"AMBIENCE OUTPUTS  |  individual wet sends; 0 = silent, 100 = full");',
'''  label(heading,"AMBIENCE OUTPUTS  |  individual wet sends; 0 = silent, 100 = full");
  label(focusTitle,"AMBIENCE EXTRACTION  |  select material for the wet speakers");
  wetOnly.onClick=[this]{cfg.ambientWetOnly=wetOnly.getToggleState();saveSettings();};''')
change('  for(int i=0;i<10;++i){','  for(int i=0;i<14;++i){')
change('   slider.setRange(0,i==3?120:(i>=4&&i<=7)?150:100,1);',
'''   if(i==12)slider.setRange(40,4000,10);
   else if(i==13)slider.setRange(1000,18000,50);
   else slider.setRange(0,i==3?120:(i>=4&&i<=7)?150:100,1);''')
change('   cfg.ambientSL=100;cfg.ambientSR=100;cfg.ambientRL=100;cfg.ambientRR=100;',
'''   cfg.ambientSL=100;cfg.ambientSR=100;cfg.ambientRL=100;cfg.ambientRR=100;
   cfg.ambientExtraction=45;cfg.ambientDuck=35;cfg.ambientLow=180;cfg.ambientHigh=8000;
   cfg.ambientWetOnly=0;''')
change('  refresh();\n }\n void resized()override{\n  auto a=getLocalBounds().reduced(17,9);',
'''  refresh();
  setSize(900,875); // The Viewport needs a real-sized component to enable scrolling.
 }
 void resized()override{
  auto a=getLocalBounds().reduced(17,9);''')
change('  for(int i=4;i<8;++i)row(i);\n  a.removeFromTop(9);reset.setBounds',
'''  for(int i=4;i<8;++i)row(i);
  a.removeFromTop(9);focusTitle.setBounds(a.removeFromTop(28));
  row(10);row(11);row(12);row(13);
  wetOnly.setBounds(a.removeFromTop(31));
  a.removeFromTop(9);reset.setBounds''')
p.write_text(s,encoding="utf-8")
assert 'surroundAmbientEngine.process(' not in s
assert 'focusProcessor.process(p,len,n,sr' in s
assert 'tab("7.1 ambience"' in s
print("PASS: focus processing routed, four UI sliders and wet-only control wired, save/load updated.")
