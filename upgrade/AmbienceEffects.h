// SPDX-License-Identifier: AGPL-3.0-or-later
// Ambient-only reverberation for stereo and discrete WAVEFORMATEXTENSIBLE 7.1.
// No UI, file I/O, allocation or locks in the realtime processing path.
#pragma once
#include <array>
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace ambiencefx {
inline float bounded(float v,float low,float high){return std::max(low,std::min(high,v));}
inline float finite(float v){return std::isfinite(v)?bounded(v,-3.f,3.f):0.f;}
constexpr float pi=3.14159265358979323846f;
struct ReverbSettings {
 bool enabled=false;
 int wet=35,decay=55,damping=45,preDelayMs=25;
 // SL, SR, RL, RR. These are WET-only sends. LFE and centre are not modified.
 int sideLeft=100,sideRight=100,rearLeft=100,rearRight=100;
};

class DiffuseReverb {
 static constexpr unsigned ring=32768,mask=ring-1;
 std::array<std::array<float,ring>,8> delay{};
 std::array<std::array<float,ring>,2> pre{};
 float damp[8]{},low[2]{};
 unsigned pos=0;
 int lastRate=0;
 bool active=false;
public:
 void reset(){
  for(auto& d:delay)d.fill(0.f);
  for(auto& d:pre)d.fill(0.f);
  for(float& v:damp)v=0.f;
  low[0]=low[1]=0;pos=0;lastRate=0;active=false;
 }
 void process(float* audio,int frames,int channels,int rate,unsigned mask71,
              const ReverbSettings& s,bool surroundOnly){
  if(!audio||frames<=0||rate<22050||rate>192000||
      (surroundOnly ? (channels!=8||mask71!=0x63f) : (channels!=2&&channels!=8)))return;
  if(!s.enabled||s.wet<=0){if(active)reset();return;}
  if(rate!=lastRate){reset();lastRate=rate;}
  active=true;
  // Delay lengths are intentionally incommensurate to avoid periodic flutter.
  constexpr float lengths[8]={29.7f,37.1f,41.1f,43.7f,53.1f,59.3f,61.7f,71.9f};
  unsigned taps[8];float feedback[8];
  const float rt60=.65f+7.15f*bounded(s.decay,0,100)*.01f;
  for(int k=0;k<8;++k){
   taps[k]=unsigned(lengths[k]*.001f*rate);
   feedback[k]=std::pow(.001f,float(taps[k])/(rate*rt60));
  }
  const unsigned pred=unsigned(bounded(s.preDelayMs,0,120)*rate*.001f);
  const float cutoff=9000.f-7300.f*bounded(s.damping,0,100)*.01f;
  const float dampCoeff=1.f-std::exp(-2.f*pi*cutoff/rate);
  const float hpCoeff=1.f-std::exp(-2.f*pi*165.f/rate);
  const float wet=bounded(s.wet,0,100)*.01f*.55f;
  const float send[4]={bounded(s.sideLeft,0,150)*.01f,bounded(s.sideRight,0,150)*.01f,
                       bounded(s.rearLeft,0,150)*.01f,bounded(s.rearRight,0,150)*.01f};
  for(int i=0;i<frames;++i){
   float* p=audio+i*channels;
   const float left=finite(p[0]),right=finite(p[1]);
   const float source[2]={left,right};
   float filtered[2];
   for(int ch=0;ch<2;++ch){
    pre[ch][pos&mask]=source[ch];
    const float delayed=pre[ch][(pos-pred)&mask];
    low[ch]+=hpCoeff*(delayed-low[ch]);
    filtered[ch]=delayed-low[ch];
   }
   const float mid=.5f*(filtered[0]+filtered[1]);
   const float side=.5f*(filtered[0]-filtered[1]);
   float tap[8];
   for(int k=0;k<8;++k){
    const float x=delay[k][(pos-taps[k])&mask];
    damp[k]+=dampCoeff*(x-damp[k]);
    tap[k]=damp[k];
   }
   float mixed[8];
   for(int k=0;k<8;++k)mixed[k]=tap[k];
   for(int width=1;width<8;width*=2){
    for(int group=0;group<8;group+=2*width){
     for(int j=0;j<width;++j){
      const float a=mixed[group+j],b=mixed[group+j+width];
      mixed[group+j]=a+b;mixed[group+j+width]=a-b;
     }
    }
   }
   constexpr float polarity[8]={1,-1,1,1,-1,1,-1,-1};
   for(int k=0;k<8;++k){
    delay[k][pos&mask]=finite(.22f*(mid+side*polarity[k])+feedback[k]*mixed[k]*.3535533906f);
   }
   // Decorrelated late reflection outputs: no direct/dry feed to surround channels.
   const float a=(tap[0]+tap[3]-tap[5]-tap[6])*.37f;
   const float b=(tap[1]-tap[2]+tap[4]-tap[7])*.37f;
   const float c=(tap[0]-tap[2]+tap[5]-tap[7])*.34f;
   const float d=(tap[1]+tap[3]-tap[4]-tap[6])*.34f;
   if(surroundOnly){
    p[6]=finite(p[6]+wet*a*send[0]); // side left
    p[7]=finite(p[7]+wet*b*send[1]); // side right
    p[4]=finite(p[4]+wet*c*send[2]); // rear left
    p[5]=finite(p[5]+wet*d*send[3]); // rear right
   }else{
    p[0]=finite(p[0]+wet*(.65f*a+.35f*c));
    p[1]=finite(p[1]+wet*(.65f*b+.35f*d));
   }
   ++pos;
  }
 }
};

struct ChorusSettings { bool enabled=false; int wet=23,rate=28; };
class SoftChorus {
 static constexpr unsigned ring=8192,mask=ring-1;
 std::array<std::array<float,ring>,2> history{};
 float phase=0.f;unsigned pos=0;int lastRate=0;bool active=false;
 static float read(const std::array<float,ring>& data,unsigned position,float lag){
  const float src=float(position)-lag;const int ix=int(std::floor(src));
  const float alpha=src-ix;
  return data[unsigned(ix)&mask]*(1.f-alpha)+data[unsigned(ix+1)&mask]*alpha;
 }
public:
 void reset(){for(auto& h:history)h.fill(0.f);pos=0;phase=0;lastRate=0;active=false;}
 void process(float* audio,int frames,int channels,int rate,const ChorusSettings& s){
  if(!audio||frames<=0||(channels!=2&&channels!=8)||rate<22050||rate>192000)return;
  if(!s.enabled||s.wet<=0){if(active)reset();return;}
  if(rate!=lastRate){reset();lastRate=rate;}
  active=true;
  const float wet=bounded(s.wet,0,100)*.01f*.38f;
  const float delta=2.f*pi*(.11f+bounded(s.rate,0,100)*.018f)/rate;
  for(int f=0;f<frames;++f){
   auto* p=audio+f*channels;
   const float x[2]={finite(p[0]),finite(p[1])};
   const unsigned at=pos&mask;
   for(int ch=0;ch<2;++ch){
    const float lag=rate*(.011f+.0035f*std::sin(phase+(ch?1.7f:0.f)));
    const float y=read(history[ch],at,lag);
    p[ch]=finite(x[ch]*(1.f-wet)+wet*y);
    history[ch][at]=x[ch];
   }
   ++pos;phase+=delta;if(phase>=2*pi)phase-=2*pi;
  }
 }
};
} // namespace ambiencefx
