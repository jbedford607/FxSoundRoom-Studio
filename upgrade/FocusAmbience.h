// SPDX-License-Identifier: AGPL-3.0-or-later
// Ambient focus: real-time side-information extraction, frequency selection,
// level-dependent wet ducking, and optional wet-only derived surround.
// Not AI source separation: stereo difference is only an approximation.
#pragma once
#include "AmbienceEffects.h"
#include <array>
#include <algorithm>
#include <cmath>

namespace ambiencefx {
struct FocusSettings {
 int extraction=45; // 0: full stereo, 100: stereo difference only
 int lowCutHz=180, highCutHz=8000;
 int duckPercent=35;
 bool wetOnly=false;
};

class FocusSend {
 // One-pole stereo bandpass state. Updated only from the render thread.
 float low[2]{},high[2]{},dryEnvelope=0;
 int lastRate=0;bool previouslyEnabled=false;
 static constexpr int maxFrames=256;
public:
 void reset(){low[0]=low[1]=high[0]=high[1]=dryEnvelope=0.f;lastRate=0;previouslyEnabled=false;}
 void process(float* dest,int frames,int channels,int rate,unsigned layout,
              const ReverbSettings& reverbSettings,const FocusSettings& focus,
              DiffuseReverb& reverb,bool derivedUpmix=false){
  if(!dest||frames<=0||frames>maxFrames||channels!=8||layout!=0x63f||
     rate<22050||rate>192000)return;
  if(!reverbSettings.enabled||reverbSettings.wet<=0){
   if(previouslyEnabled){reset();reverb.reset();}
   return;
  }
  if(lastRate!=rate){reset();reverb.reset();lastRate=rate;}
  previouslyEnabled=true;
  const float extraction=bounded(focus.extraction,0,100)*.01f;
  const int lowHz=int(bounded(float(focus.lowCutHz),40.f,4000.f));
  const int highHz=int(bounded(float(focus.highCutHz),float(lowHz+150),18000.f));
  const float lowAlpha=1.f-std::exp(-2.f*pi*lowHz/rate);
  const float highAlpha=1.f-std::exp(-2.f*pi*highHz/rate);
  const float attack=1.f-std::exp(-1.f/(rate*.008f));
  const float release=1.f-std::exp(-1.f/(rate*.24f));
  const float duck=bounded(focus.duckPercent,0,100)*.01f;
  std::array<float,maxFrames*8> wet{};
  std::array<float,maxFrames> duckGain{};
  std::array<bool,maxFrames> preserveNative{};
  for(int i=0;i<frames;++i){
   const float* src=dest+i*8;
   const float l=finite(src[0]),r=finite(src[1]);
   const float side=.5f*(l-r);
   const float mono=.5f*(std::abs(l)+std::abs(r));
   // Fast attack / slow release: loud direct passages push wet ambience down,
   // and the reverb becomes audible again after a transient.
   dryEnvelope+=(mono>dryEnvelope?attack:release)*(mono-dryEnvelope);
   duckGain[i]=1.f/(1.f+14.f*duck*dryEnvelope);
   const float selected[2]={
     (1.f-extraction)*l+extraction*side,
     (1.f-extraction)*r-extraction*side
   };
   for(int ch=0;ch<2;++ch){
    low[ch]+=lowAlpha*(selected[ch]-low[ch]);
    const float hp=selected[ch]-low[ch];
    high[ch]+=highAlpha*(hp-high[ch]);
    wet[i*8+ch]=finite(high[ch]);
   }
   // Protect real multichannel content; wet-only clears synthesized surround,
   // not native side/rear audio when input already contains discrete material.
   preserveNative[i]=std::abs(src[4])+std::abs(src[5])+
                     std::abs(src[6])+std::abs(src[7])>1.e-6f;
  }
  reverb.process(wet.data(),frames,8,rate,layout,reverbSettings,true);
  for(int i=0;i<frames;++i){
   float* dst=dest+i*8;
   if(focus.wetOnly&&derivedUpmix&&!preserveNative[i]){
    for(int c=4;c<8;++c)dst[c]=0.f;
   }
   for(int c=4;c<8;++c)dst[c]=finite(dst[c]+wet[i*8+c]*duckGain[i]);
  }
 }
};
} // namespace ambiencefx
