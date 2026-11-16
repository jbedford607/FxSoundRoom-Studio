#include "AmbienceEffects.h"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
int main(){
 constexpr int rate=48000;
 static ambiencefx::DiffuseReverb stereo,surround;
 static ambiencefx::SoftChorus chorus;
 std::vector<float> two(48000*2,0.f);
 ambiencefx::ReverbSettings r;
 two[0]=.75f;two[1]=.75f;
 auto original=two;
 stereo.process(two.data(),48000,2,rate,3,r,false);
 assert(two==original); // disabled = bit-for-bit bypass
 r.enabled=true;r.wet=65;r.decay=75;r.preDelayMs=35;
 stereo.process(two.data(),48000,2,rate,3,r,false);
 assert(two[0]==.75f&&two[1]==.75f); // dry attack preserved
 double tail=0;
 for(size_t i=10000;i<two.size();++i){assert(std::isfinite(two[i]));tail+=std::abs(two[i]);}
 assert(tail>.01); // audible non-trivial reverb tail
 std::vector<float> many(2*48000*2,0.f);
 many[0]=many[1]=.5f;
 surround.reset();
 std::vector<float> eight(96000*8,0.f);
 eight[0]=eight[1]=.75f;
 r.sideLeft=100;r.sideRight=100;r.rearLeft=100;r.rearRight=100;
 surround.process(eight.data(),96000,8,rate,0x63f,r,true);
 for(int i=0;i<96000;++i){
  assert(eight[8*i+0]==(i==0?.75f:0.f));
  assert(eight[8*i+1]==(i==0?.75f:0.f));
  assert(eight[8*i+2]==0.f);assert(eight[8*i+3]==0.f);
 }
 double wetSide=0,wetRear=0;
 for(int i=3000;i<96000;++i){
  wetSide+=std::abs(eight[8*i+6])+std::abs(eight[8*i+7]);
  wetRear+=std::abs(eight[8*i+4])+std::abs(eight[8*i+5]);
 }
 assert(wetSide>.01 && wetRear>.01);
 // Turning a side wet-send OFF must silence only that path.
 surround.reset();std::fill(eight.begin(),eight.end(),0.f);
 eight[0]=eight[1]=.75f;r.sideLeft=0;
 surround.process(eight.data(),96000,8,rate,0x63f,r,true);
 for(int i=0;i<96000;++i)assert(eight[8*i+6]==0.f);
 // No surround output for unsupported speaker layouts.
 surround.reset();std::fill(eight.begin(),eight.end(),0.f);eight[0]=.5f;
 auto untouched=eight;
 surround.process(eight.data(),96000,8,rate,0x3f,r,true);
 assert(eight==untouched);
 // Chorus should not touch centre, sub, or rear channels.
 ambiencefx::ChorusSettings c;c.enabled=true;c.wet=70;
 static std::vector<float> chorusData(48000*8,0.f);
 for(int i=0;i<48000;++i){chorusData[8*i]=.3f*std::sin(i*.041f);chorusData[8*i+1]=.2f*std::sin(i*.047f);chorusData[8*i+4]=.17f;}
 auto dry=chorusData;chorus.process(chorusData.data(),48000,8,rate,c);
 double change=0;
 for(int i=0;i<48000;++i){
  change+=std::abs(chorusData[i*8]-dry[i*8]);
  for(int ch=2;ch<8;++ch)assert(chorusData[i*8+ch]==dry[i*8+ch]);
 }
 assert(change>.01);
 std::puts("PASS ambient DSP: transparent bypass, true decay, dry preservation, mono reverb, 7.1 wet routing and isolated sends, layout safety, chorus");
}
