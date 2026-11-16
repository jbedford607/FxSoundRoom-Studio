#include "AdvancedEffects.h"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
int main(){
 static freshfx::StereoRack stereo;
 static freshfx::SurroundOrbit orbit;
 const int rate=48000;
 std::vector<float> eight(512*8),two(512*2);
 freshfx::StereoSettings s;
 for(int i=0;i<512;++i){eight[i*8]=.3f;eight[i*8+1]=-.2f;}
 auto initial=eight;
 stereo.process(eight.data(),512,8,rate,s);
 assert(eight==initial); // transparent default bypass
 s.width=0;
 stereo.process(eight.data(),512,8,rate,s);
 for(int i=0;i<512;++i){assert(std::abs(eight[i*8]-eight[i*8+1])<1e-6);
  for(int ch=2;ch<8;++ch)assert(eight[i*8+ch]==initial[i*8+ch]);}
 stereo.reset();s={};s.chorus=true;s.chorusWet=80;s.chorusRate=55;
 double chorusDifference=0;
 for(int b=0;b<85;++b){
  for(int i=0;i<512;++i){two[2*i]=.22f*std::sin((b*512+i)*.064f);two[2*i+1]=.25f*std::sin((b*512+i)*.071f);}
  auto dry=two;stereo.process(two.data(),512,2,rate,s);
  for(size_t i=0;i<two.size();++i){assert(std::isfinite(two[i]));chorusDifference+=std::abs(two[i]-dry[i]);}
 }
 assert(chorusDifference>10.);
 stereo.reset();s={};s.echo=true;s.echoDelay=100;s.echoWet=90;s.echoFeedback=55;
 std::vector<float> delayed(9000*2,0.f);delayed[0]=.8f;
 stereo.process(delayed.data(),9000,2,rate,s);
 assert(std::abs(delayed[0]-.8f)<.001f);
 assert(std::abs(delayed[4800*2+1])>.05f); // impulse crosses left -> right
 assert(std::abs(delayed[4800*2])<.001f);
 stereo.reset();s={};s.phaser=true;s.phaserWet=85;
 double difference=0;
 for(int b=0;b<85;++b){
  for(int i=0;i<512;++i){two[2*i]=two[2*i+1]=.25f*std::sin((b*512+i)*.048f);}
  auto dry=two;stereo.process(two.data(),512,2,rate,s);
  for(size_t i=0;i<two.size();++i){assert(std::isfinite(two[i]));difference+=std::abs(two[i]-dry[i]);}
 }
 assert(difference>10.);
 freshfx::OrbitSettings o;
 std::fill(eight.begin(),eight.end(),0.f);eight[0]=.7f;
 initial=eight;
 orbit.process(eight.data(),512,8,rate,0x63f,o);
 assert(eight==initial);
 orbit.reset();o.enabled=true;o.delayMs=100;o.wet=90;o.speed=60;
 std::vector<float> around(48000*3*8,0.f);
 around[0]=.8f;around[1]=.8f;
 orbit.process(around.data(),48000*3,8,rate,0x63f,o);
 bool heardSideOrRear=false,heardCenter=false;
 for(size_t i=0;i<around.size()/8;i++){
  for(int ch:{4,5,6,7})heardSideOrRear|=std::abs(around[i*8+ch])>0.0001f;
  heardCenter|=around[i*8+2]!=0.f;
  for(int ch=0;ch<8;ch++)assert(std::isfinite(around[i*8+ch]));
 }
 assert(heardSideOrRear&&!heardCenter); // no echo into center or LFE
 orbit.reset();std::fill(eight.begin(),eight.end(),0.f);eight[0]=.9f;initial=eight;
 orbit.process(eight.data(),512,2,rate,3,o);
 assert(eight==initial); // 7.1 effects must not process unsupported layouts
 std::puts("PASS Stereo/7.1: bypass, width, chorus, ping-pong echo, phaser, rotating surround, safety");
}
