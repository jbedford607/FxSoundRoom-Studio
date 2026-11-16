// SPDX-License-Identifier: AGPL-3.0-or-later
// Native realtime stereo/7.1 effects; no plugin host or allocations in process().
#pragma once
#include <array>
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace freshfx {
inline float clamp(float x, float lo, float hi) { return std::max(lo, std::min(hi, x)); }
inline float safe(float x) { return std::isfinite(x) ? clamp(x, -4.f, 4.f) : 0.f; }
constexpr float twoPi = 6.283185307179586f;
struct StereoSettings {
 bool chorus=false, echo=false, phaser=false;
 int chorusWet=35, chorusRate=35, echoWet=35, echoDelay=280, echoFeedback=42;
 int phaserWet=35, phaserRate=35, width=100;
};
class StereoRack {
 static constexpr unsigned delaySize=262144, chorusSize=8192;
 static constexpr unsigned delayMask=delaySize-1, chorusMask=chorusSize-1;
 std::array<std::array<float,delaySize>,2> echoBuffer{};
 std::array<std::array<float,chorusSize>,2> chorusBuffer{};
 std::array<std::array<float,4>,2> phaserState{};
 unsigned pos=0;int lastRate=0;float chorusPhase=0,phaserPhase=0;
 static float sample(const std::array<float,chorusSize>& line,unsigned write,float lag){
  float read=float(write)-lag;auto whole=int(std::floor(read));
  float f=read-float(whole);
  return line[unsigned(whole)&chorusMask]*(1.f-f)+line[unsigned(whole+1)&chorusMask]*f;
 }
public:
 void reset(){
  for(auto& a:echoBuffer)a.fill(0);
  for(auto& a:chorusBuffer)a.fill(0);
  for(auto& a:phaserState)a.fill(0);
  lastRate=0;pos=0;chorusPhase=phaserPhase=0;
 }
 void process(float* audio,int frames,int channels,int rate,const StereoSettings& c){
  if(!audio||frames<=0||(channels!=2&&channels!=8)||rate<22050||rate>192000)return;
  if(!c.chorus&&!c.echo&&!c.phaser&&c.width==100)return;
  if(lastRate!=rate){reset();lastRate=rate;}
  const float cw=clamp(c.chorusWet,0,100)*.006f;
  const float ew=clamp(c.echoWet,0,100)*.005f;
  const float pw=clamp(c.phaserWet,0,100)*.0065f;
  const float feedback=clamp(c.echoFeedback,0,80)*.01f;
  const unsigned echoLag=unsigned(clamp(c.echoDelay,65,900)*rate/1000.f);
  const float chorusIncrement=twoPi*(.1f+clamp(c.chorusRate,0,100)*.038f)/rate;
  const float phaserIncrement=twoPi*(.04f+clamp(c.phaserRate,0,100)*.024f)/rate;
  const float width=clamp(c.width,0,180)*.01f;
  for(int i=0;i<frames;++i){
   float* p=audio+i*channels;
   const unsigned ep=pos&delayMask,cp=pos&chorusMask;
   float in[2]={safe(p[0]),safe(p[1])}, out[2]={in[0],in[1]};
   if(c.chorus){
    for(int ch=0;ch<2;++ch){
     const float lag=rate*(.010f+.004f*std::sin(chorusPhase+(ch?1.9f:0.f)));
     const float delayed=sample(chorusBuffer[ch],cp,lag);
     out[ch]=out[ch]*(1.f-.35f*cw)+delayed*cw;
    }
   }
   if(c.phaser){
    for(int ch=0;ch<2;++ch){
     const float hz=300.f+1800.f*(.5f+.5f*std::sin(phaserPhase+(ch?1.5707963f:0.f)));
     const float t=std::tan(3.14159265f*hz/rate);
     const float a=clamp((1.f-t)/(1.f+t),-.99f,.99f);
     float y=out[ch];
     for(int stage=0;stage<4;++stage){
      float z=-a*y+phaserState[ch][stage];
      phaserState[ch][stage]=y+a*z;
      y=z;
     }
     out[ch]=out[ch]*(1.f-pw)+y*pw;
    }
   }
   if(c.echo){
    // Cross-feed produces a true left/right ping-pong echo.
    float a=echoBuffer[0][(ep-echoLag)&delayMask];
    float b=echoBuffer[1][(ep-echoLag)&delayMask];
    echoBuffer[0][ep]=safe(.52f*out[0]+feedback*b);
    echoBuffer[1][ep]=safe(.52f*out[1]+feedback*a);
    out[0]+=ew*b;out[1]+=ew*a;
   }
   if(c.width!=100){
    float mid=.5f*(out[0]+out[1]),side=.5f*(out[0]-out[1])*width;
    out[0]=mid+side;out[1]=mid-side;
   }
   p[0]=safe(out[0]);p[1]=safe(out[1]);
   chorusBuffer[0][cp]=in[0];chorusBuffer[1][cp]=in[1];
   chorusPhase+=chorusIncrement;phaserPhase+=phaserIncrement;
   if(chorusPhase>=twoPi)chorusPhase-=twoPi;
   if(phaserPhase>=twoPi)phaserPhase-=twoPi;
   ++pos;
  }
 }
};
struct OrbitSettings {
 bool enabled=false;int wet=35,delayMs=270,feedback=42,speed=25;
};
class SurroundOrbit {
 static constexpr unsigned size=262144,mask=size-1;
 std::array<float,size> echo{};
 unsigned pos=0;int lastRate=0;float phase=0,bass=0;
public:
 void reset(){echo.fill(0);pos=0;lastRate=0;phase=0;bass=0;}
 void process(float* p,int frames,int channels,int rate,unsigned speakerMask,const OrbitSettings& c){
  if(!p||frames<=0||channels!=8||speakerMask!=0x63f||rate<22050||rate>192000||!c.enabled)return;
  if(lastRate!=rate){reset();lastRate=rate;}
  const int routes[6]={0,6,4,5,7,1};
  const unsigned lag=unsigned(clamp(c.delayMs,65,900)*rate*.001f);
  const float wet=clamp(c.wet,0,100)*.005f;
  const float fb=clamp(c.feedback,0,75)*.01f;
  const float move=twoPi*(.03f+clamp(c.speed,0,100)*.014f)/rate;
  const float bassCoeff=1.f-std::exp(-twoPi*130.f/rate);
  for(int i=0;i<frames;++i){
   auto* x=p+i*8;
   const float mid=.5f*(safe(x[0])+safe(x[1]))+.18f*safe(x[2]);
   bass+=bassCoeff*(mid-bass);
   const float input=mid-bass;
   const unsigned at=pos&mask;
   const float delayed=echo[(pos-lag)&mask];
   echo[at]=safe(.42f*input+fb*delayed);
   const float speaker=phase*(6.f/twoPi);
   const int left=int(speaker)%6;
   const float fraction=speaker-float(int(speaker));
   // Equal-power movement across all six full-range speakers (never into LFE).
   const float a=std::cos(fraction*1.5707963268f);
   const float b=std::sin(fraction*1.5707963268f);
   x[routes[left]]=safe(x[routes[left]]+wet*delayed*a);
   x[routes[(left+1)%6]]=safe(x[routes[(left+1)%6]]+wet*delayed*b);
   phase+=move;if(phase>=twoPi)phase-=twoPi;
   ++pos;
  }
 }
};
} // namespace freshfx
