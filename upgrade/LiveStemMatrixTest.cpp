#include "LiveStemMatrix.h"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>

static constexpr int rate=48000;
static constexpr int block=256;
static stems71::Extractor processor;
static stems71::Settings settings;
static void run(float hz,float leftScale,float rightScale,int repeats){
 float stereo[block*2]{};
 float out[block*8]{};
 for(int r=0;r<repeats;++r){
  for(int i=0;i<block;++i){
   float v=.55f*std::sin(6.283185307179586f*hz*(r*block+i)/rate);
   stereo[2*i]=leftScale*v;
   stereo[2*i+1]=rightScale*v;
  }
  std::fill(out,out+block*8,0.f);
  processor.process(stereo,out,block,rate,0x63f,true,settings);
  for(float x:out)assert(std::isfinite(x)&&std::abs(x)<=.981f);
 }
}
int main(){
 float stereo[block*2]{},out[block*8]{};
 // Disabled and non-stereo-derived source are strict bypass.
 std::fill(out,out+block*8,.21f);
 auto old=std::vector<float>(out,out+block*8);
 processor.process(stereo,out,block,rate,0x63f,true,settings);
 assert(std::equal(out,out+block*8,old.begin()));
 settings.enabled=true;
 processor.process(stereo,out,block,rate,0x63f,false,settings);
 assert(std::equal(out,out+block*8,old.begin()));
 processor.process(stereo,out,block,rate,0x3f,true,settings);
 assert(std::equal(out,out+block*8,old.begin()));
 // Bass is present with low frequencies, much weaker with 1.5kHz tones.
 settings.replaceSynthesizedSides=false;
 settings.routes={uint8_t(1u<<3),0,0,0};
 processor.reset();run(75.f,1.f,1.f,40);
 const float low=processor.meter(stems71::Bass);
 processor.reset();run(1500.f,1.f,1.f,40);
 const float high=processor.meter(stems71::Bass);
 assert(low>.08f && high < low*.15f);
 // Mid-panned voice estimate goes to the centre, not to side difference.
 settings.routes={0,uint8_t(1u<<2),0,0};
 processor.reset();run(850.f,1.f,1.f,40);
 assert(processor.meter(stems71::Center)>.08f);
 assert(processor.meter(stems71::StereoSides)<.0001f);
 // Anti-correlated stereo content produces a non-zero stereo-side stem,
 // but no centre-panned music or bass.
 settings.routes={0,0,0,uint8_t((1u<<6)|(1u<<7))};
 processor.reset();run(1300.f,1.f,-1.f,40);
 assert(processor.meter(stems71::StereoSides)>.1f);
 assert(processor.meter(stems71::Center)<.0001f);
 // A transient strongly excites percussion, which dies away on sustained tones.
 settings.routes={0,0,uint8_t((1u<<4)|(1u<<5)),0};
 processor.reset();
 std::fill(stereo,stereo+block*2,0.f);
 stereo[0]=1.f;stereo[1]=1.f;
 std::fill(out,out+block*8,0.f);
 processor.process(stereo,out,block,rate,0x63f,true,settings);
 const float transient=processor.meter(stems71::Transients);
 assert(transient>.05f);
 run(900.f,1.f,1.f,60);
 assert(processor.meter(stems71::Transients)<transient*.7f);
 // Matrix routes only enabled channels, and does not overwrite fronts in normal mode.
 settings.routes={uint8_t(1u<<3),0,0,0};
 processor.reset();
 for(int i=0;i<block;++i){stereo[i*2]=stereo[i*2+1]=.65f;}
 std::fill(out,out+block*8,.11f);
 processor.process(stereo,out,block,rate,0x63f,true,settings);
 assert(out[0]==.11f && out[1]==.11f && out[2]==.11f);
 assert(out[4]==.11f && out[6]==.11f);
 // An instrument SOLO truly drops all original source channels.
 settings.preview=1;
 processor.reset();
 std::fill(out,out+block*8,.45f);
 processor.process(stereo,out,block,rate,0x63f,true,settings);
 for(int i=0;i<block;++i)for(int ch=0;ch<8;++ch)
  if(ch!=3)assert(out[i*8+ch]==0.f);
 // Replace mode clears ONLY the synthesized side/rear feeds and respects
 // user-chosen routes. Centre / sub / fronts keep the original music.
 settings.preview=0;
 settings.replaceSynthesizedSides=true;
 settings.routes={0,0,0,0};
 processor.reset();std::fill(out,out+block*8,.2f);
 processor.process(stereo,out,block,rate,0x63f,true,settings);
 for(int i=0;i<block;++i){
  for(int ch=0;ch<4;++ch)assert(out[i*8+ch]==.2f);
  for(int ch=4;ch<8;++ch)assert(out[i*8+ch]==0.f);
 }
 // Native 7.1 is never overwritten (caller supplies derived-source classification).
 processor.reset();std::fill(out,out+block*8,.2f);
 processor.process(stereo,out,block,rate,0x63f,false,settings);
 for(float sample:out)assert(sample==.2f);
 puts("PASS live stem DSP: bypass, native protection, bass selectivity, center/side, drum transients, speaker routing, SOLO, replace mode");
}
