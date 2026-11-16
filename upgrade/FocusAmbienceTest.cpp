// Native surround focus regression suite. Runs on Windows and Linux.
#include "FocusAmbience.h"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
#include <algorithm>
#include <numeric>
static constexpr int rate=48000, seconds=2, frames=rate*seconds;
static std::vector<float> signal(float frequency,float sideScale=1.f,float amp=.4f){
 std::vector<float> audio(frames*8,0.f);
 for(int i=0;i<frames;++i){
  audio[8*i]=amp*std::sin(2*ambiencefx::pi*frequency*i/rate);
  audio[8*i+1]=sideScale*audio[8*i];
 }
 return audio;
}
static double surroundEnergy(const std::vector<float>& x,int first=rate/4){
 double e=0;for(int i=first;i<frames;++i)for(int c=4;c<8;++c)e+=double(x[8*i+c])*x[8*i+c];
 return e/std::max(1,frames-first);
}
static void apply(std::vector<float>& x,ambiencefx::FocusSettings focus,
                  bool wetOnly=false, bool upmixed=true){
 static ambiencefx::FocusSend send;
 static ambiencefx::DiffuseReverb rv;
 send.reset();rv.reset();
 ambiencefx::ReverbSettings s;s.enabled=true;s.wet=90;s.decay=65;
 s.preDelayMs=10;s.sideLeft=100;s.sideRight=100;s.rearLeft=100;s.rearRight=100;
 focus.wetOnly=wetOnly;
 for(int off=0;off<frames;off+=256)
  send.process(x.data()+off*8,std::min(256,frames-off),8,rate,0x63f,s,focus,upmixed);
}
int main(){
 ambiencefx::FocusSettings f;
 static ambiencefx::FocusSend send;
 static ambiencefx::DiffuseReverb rv;
 auto bypass=signal(550.f);
 bypass[4]=.21f;
 auto backup=bypass;
 ambiencefx::ReverbSettings disabled;
 send.process(bypass.data(),256,8,rate,0x63f,disabled,f,true);
 assert(bypass==backup);
 auto wetOnly=signal(500.f,.4f);
 for(int i=0;i<frames;++i){wetOnly[8*i+6]=.13f;wetOnly[8*i+4]=.17f;}
 apply(wetOnly,f,true,true);
 double tail=surroundEnergy(wetOnly);
 assert(tail>1.e-10);
 for(int i=0;i<frames;++i){
  assert(wetOnly[8*i+0]==backup[8*i+0] || std::abs(wetOnly[8*i+0]-.4f*std::sin(2*ambiencefx::pi*500*i/rate))<2.e-5f);
  assert(wetOnly[8*i+2]==0.f && wetOnly[8*i+3]==0.f);
 }
 assert(std::abs(wetOnly[4])<1.e-7f && std::abs(wetOnly[6])<1.e-7f);
 // Native 7.1 content must survive when the incoming stream is not a stereo upmix.
 auto native=signal(500.f,.4f);
 for(int i=0;i<frames;++i)native[8*i+4]=.17f;
 apply(native,f,true,false);
 assert(std::abs(native[4]-.17f)<1.e-6f);
 // Stereo difference extraction: centre-only mono produces no late tail at 100%.
 auto mono=signal(750.f,1.f);
 f.extraction=100;
 apply(mono,f);
 const double centerOnly=surroundEnergy(mono);
 auto stereoDifference=signal(750.f,-.7f);
 apply(stereoDifference,f);
 const double difference=surroundEnergy(stereoDifference);
 assert(difference>1.e-9 && centerOnly<difference*.001);
 // Band selection suppresses bass input substantially; 1.2 kHz passes.
 f.extraction=0;f.lowCutHz=550;f.highCutHz=5000;
 auto bass=signal(70.f,.5f);
 apply(bass,f);
 auto mids=signal(1200.f,.5f);
 apply(mids,f);
 const double bassPower=surroundEnergy(bass),midPower=surroundEnergy(mids);
 assert(midPower>bassPower*2.);
 // Ducking reduces wet level while loud direct audio is present.
 f.lowCutHz=180;f.highCutHz=8000;f.duckPercent=0;
 auto unDucked=signal(600.f,.3f,.8f);
 apply(unDucked,f);
 const double before=surroundEnergy(unDucked,rate);
 f.duckPercent=100;
 auto ducked=signal(600.f,.3f,.8f);
 apply(ducked,f);
 const double after=surroundEnergy(ducked,rate);
 assert(after<before*.5 && after>0);
 // Never modify other layouts.
 auto wrong=signal(900.f,.2f);
 auto old=wrong;
 send.reset();rv.reset();
 ambiencefx::ReverbSettings on;on.enabled=true;
 send.process(wrong.data(),256,8,rate,0x3f,on,f,true);
 assert(wrong==old);
 std::printf("PASS focus: bypass, wet-only stereo, native 7.1, extraction, frequency selection, ducking, layout safety\n");
}
