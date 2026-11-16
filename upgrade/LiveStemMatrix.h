// SPDX-License-Identifier: AGPL-3.0-or-later
// Low-latency DSP stem ESTIMATES for stereo music feeding a 7.1 endpoint.
// These are not neural-network or true instrument-isolated stems.
// No file I/O, allocation, FFT buffering, locks or GUI calls on the audio thread.
#pragma once
#include <array>
#include <atomic>
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace stems71 {
constexpr unsigned speakerLayout=0x63fu; // Windows 7.1: FL FR C LFE BL BR SL SR
constexpr int channels=8;
constexpr int stemCount=4;
enum Stem {Bass=0,Center=1,Transients=2,StereoSides=3};
constexpr uint8_t defaultMask[4]={uint8_t(1u<<3),uint8_t(1u<<2),
 uint8_t((1u<<4)|(1u<<5)),uint8_t((1u<<6)|(1u<<7))};
constexpr int defaultGain[4]={65,50,55,55};
inline float clamp(float x,float low,float high){return std::max(low,std::min(high,x));}
inline float finite(float x){return std::isfinite(x)?clamp(x,-2.f,2.f):0.f;}
inline float coeff(float hz,int rate) {
 return 1.f-std::exp(-6.2831853071795864769f*hz/float(rate));
}
struct Settings {
 bool enabled=false;
 bool replaceSynthesizedSides=true; // Preserve native 7.1: route only stereo-derived input.
 int preview=0; // 0: normal music, 1..4: listen ONLY to an estimated stem.
 int bassCutHz=125;
 int centerFocus=55;
 int percussionFocus=65;
 std::array<uint8_t,4> routes={defaultMask[0],defaultMask[1],defaultMask[2],defaultMask[3]};
 std::array<int,4> levels={defaultGain[0],defaultGain[1],defaultGain[2],defaultGain[3]};
};

class Extractor {
 float bass1=0,bass2=0,midLow=0,midHigh=0,sideLow=0;
 float centreEnergy=0,sideEnergy=0,transientFast=0,transientSlow=0;
 int lastRate=0;
 std::array<std::atomic<float>,4> levels{};
public:
 void reset(){
  bass1=bass2=midLow=midHigh=sideLow=0.f;
  centreEnergy=sideEnergy=transientFast=transientSlow=0.f;
  lastRate=0;
  for(auto& m:levels)m.store(0.f,std::memory_order_relaxed);
 }
 // Read from the UI timer; approximate peak for the latest 256-frame chunk.
 float meter(int stem)const{
  return stem>=0&&stem<4?levels[stem].load(std::memory_order_relaxed):0.f;
 }
 void process(const float* originalLR,float* surround,int frames,int rate,unsigned mask,
              bool stereoDerived,const Settings& s){
  if(!originalLR||!surround||frames<=0||frames>256||rate<22050||rate>192000||
     mask!=speakerLayout)return;
  if(!s.enabled||!stereoDerived){
   for(auto& m:levels)m.store(0.f,std::memory_order_relaxed);
   return;
  }
  if(lastRate!=rate){reset();lastRate=rate;}
  const int cutoff=std::max(55,std::min(240,s.bassCutHz));
  const float aBass=coeff(float(cutoff),rate);
  const float aLow=coeff(160.f,rate),aHigh=coeff(4800.f,rate);
  const float aSide=coeff(210.f,rate),aEnv=coeff(17.f,rate);
  const float aFast=1.f-std::exp(-1.f/(.0025f*rate));
  const float aSlow=1.f-std::exp(-1.f/(.075f*rate));
  const float centreStrength=clamp(s.centerFocus*.01f,0.f,1.f);
  const float percussionStrength=clamp(s.percussionFocus*.01f,0.f,1.f);
  float gains[4];
  uint8_t routes[4];
  for(int k=0;k<4;++k){
   gains[k]=clamp(float(s.levels[k]),0.f,150.f)*.01f;
   routes[k]=s.routes[k];
  }
  const bool monitoring=s.preview>0&&s.preview<=4;
  float peak[4]={};
  for(int i=0;i<frames;++i){
   const float left=finite(originalLR[2*i]),right=finite(originalLR[2*i+1]);
   float* dest=surround+i*8;
   const float mid=(left+right)*.5f;
   const float side=(left-right)*.5f;
   // Bass: dual cascaded low-passes. Works for kicks AND pitched bass.
   bass1+=aBass*(mid-bass1);bass2+=aBass*(bass1-bass2);
   const float bass=bass2;
   // Center: shared L/R content with bass removed and a 4.8 kHz roll-off.
   midLow+=aLow*(mid-midLow);
   midHigh+=aHigh*(mid-midLow-midHigh);
   centreEnergy+=aEnv*(std::abs(mid)-centreEnergy);
   sideEnergy+=aEnv*(std::abs(side)-sideEnergy);
   const float dominance=clamp((centreEnergy-.35f*centreStrength*sideEnergy)/
                                    (centreEnergy+.001f),0.f,1.f);
   const float center=midHigh*dominance;
   // Percussive estimate: transient excess (2.5ms vs. 75ms envelope).
   const float highPassed=mid-midLow;
   transientFast+=aFast*(std::abs(highPassed)-transientFast);
   transientSlow+=aSlow*(std::abs(highPassed)-transientSlow);
   const float novelty=clamp((transientFast-1.08f*transientSlow)/
                              (transientFast+.0001f),0.f,1.f);
   const float percussion=highPassed*clamp(novelty*(.75f+2.5f*percussionStrength),0.f,1.f);
   // Stereo side content: stereo-difference information, high-passed to avoid
   // routing bass out of phase into two opposite speakers.
   sideLow+=aSide*(side-sideLow);
   const float background=side-sideLow;
   const float stems[4]={bass,center,percussion,background};
   for(int k=0;k<4;++k)peak[k]=std::max(peak[k],std::abs(stems[k]));
   if(monitoring){
    for(int ch=0;ch<8;++ch)dest[ch]=0.f; // Genuine stem audition (no dry bleed).
   }else if(s.replaceSynthesizedSides){
    for(int ch=4;ch<8;++ch)dest[ch]=0.f;
   }
   for(int k=0;k<4;++k){
    if(monitoring && s.preview!=k+1)continue;
    uint8_t route=routes[k];
    const float val=stems[k]*gains[k];
    if(std::abs(val)<1.e-10f)continue;
    for(int ch=0;ch<8;++ch){
     if(!(route&(1u<<ch)))continue;
     float v=val;
     // Restore natural polarity for L/R stereo-difference sends.
     if(k==StereoSides && (ch==1||ch==5||ch==7))v=-v;
     dest[ch]=finite(dest[ch]+v);
    }
   }
   // Hard clip only touched channels: no uncontrolled output overload.
   for(int ch=0;ch<8;++ch){
    bool changed=monitoring || (s.replaceSynthesizedSides&&ch>=4);
    if(!changed)for(int k=0;k<4;++k)if((!monitoring||s.preview==k+1)&&
       (routes[k]&(1u<<ch))) {changed=true;break;}
    if(changed)dest[ch]=clamp(dest[ch],-.98f,.98f);
   }
  }
  for(int k=0;k<4;++k)levels[k].store(peak[k],std::memory_order_relaxed);
 }
};
} // namespace stems71
