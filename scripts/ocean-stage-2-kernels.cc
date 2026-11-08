// Bounded-memory numerical kernels. Scientific definitions are in ocean_stage_2.py.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>
#include <limits>

extern "C" void climate(int n, int years, const float* input,
                         float* means, float* thresholds, uint16_t* counts,
                         uint8_t* year_counts) {
  const float missing = std::numeric_limits<float>::quiet_NaN();
  #pragma omp parallel for schedule(dynamic, 8)
  for (int c = 0; c < n; ++c) {
    float m[366], q[366]; uint16_t ns[366]; uint8_t ys[366];
    std::vector<float> pool; pool.reserve(years * 11);
    for (int d = 0; d < 365; ++d) {
      pool.clear(); double sum = 0; int have_years = 0;
      for (int y = 0; y < years; ++y) {
        bool have = false;
        for (int k = -5; k <= 5; ++k) {
          const float v = input[(static_cast<size_t>(c)*years+y)*365+(d+k+365)%365];
          if (std::isfinite(v)) { pool.push_back(v); sum += v; have = true; }
        }
        have_years += have;
      }
      int s = d < 59 ? d : d+1;
      ns[s] = pool.size(); ys[s] = have_years; m[s] = q[s] = missing;
      if (have_years < 24 || pool.size() < std::ceil(.8*years*11)) continue;
      m[s] = sum / pool.size();
      double rank = .9*(pool.size()-1); int lo = std::floor(rank), hi = std::ceil(rank);
      std::nth_element(pool.begin(),pool.begin()+hi,pool.end());
      float lower = hi == lo ? pool[hi] : *std::max_element(pool.begin(),pool.begin()+hi);
      q[s] = lower + (rank-lo)*(pool[hi]-lower);
    }
    m[59]=(m[58]+m[60])/2; q[59]=(q[58]+q[60])/2;
    ns[59]=std::min(ns[58],ns[60]); ys[59]=std::min(ys[58],ys[60]);
    for (int d=0; d<366; ++d) {
      double sm=0,sq=0; uint16_t nc=65535; uint8_t yc=255;
      for(int k=-15;k<=15;++k) {
        int j=(d+k+366)%366; sm+=m[j]; sq+=q[j];
        nc=std::min(nc,ns[j]); yc=std::min(yc,ys[j]);
      }
      size_t o=static_cast<size_t>(c)*366+d;
      means[o]=sm/31; thresholds[o]=sq/31; counts[o]=nc; year_counts[o]=yc;
    }
  }
}

// Flags: 1 eligible, 2 above threshold, 4 event span, 8 start, 16 end,
// 32 pending short run at an unobserved edge. Missing days never bridge.
extern "C" void events(int n, int days, const float* input, const float* threshold,
                        const int32_t* slots, uint8_t* flags) {
  #pragma omp parallel for schedule(dynamic,32)
  for(int c=0;c<n;++c) {
    const float* a=input+static_cast<size_t>(c)*days;
    const float* q=threshold+static_cast<size_t>(c)*366;
    uint8_t* f=flags+static_cast<size_t>(c)*days;
    std::vector<std::pair<int,int>> runs;
    for(int t=0;t<days;++t) f[t]=std::isfinite(a[t])&&std::isfinite(q[slots[t]]) ? (a[t]>q[slots[t]] ? 3:1):0;
    for(int t=0;t<days;) {
      if(!(f[t]&2)) {++t;continue;}
      int s=t;while(t<days&&(f[t]&2))++t;int e=t-1;
      if(e-s+1>=5) runs.emplace_back(s,e);
      else if(s==0||e==days-1||!f[s-1]||!f[e+1]) for(int j=s;j<=e;++j)f[j]|=32;
    }
    std::vector<std::pair<int,int>> joined;
    for(auto r:runs) {
      bool bridge=!joined.empty()&&r.first-joined.back().second-1<=2;
      if(bridge)for(int j=joined.back().second+1;j<r.first;++j)if(!(f[j]&1))bridge=false;
      if(bridge)joined.back().second=r.second; else joined.push_back(r);
    }
    for(auto r:joined) {
      for(int j=r.first;j<=r.second;++j) f[j]|=4;
      f[r.first]|=8;f[r.second]|=16;
    }
  }
}

// Thermal fields: amplitude, threshold, baseline onset/end slot, onset departure,
// length, length departure, observed warm days, valid days, available days,
// status (0 complete; 1 weak; 2 baseline missing; 3 multiple baseline seasons;
// 4 onset absent; 5 missing target; 6 open end; 7 multiple target seasons).
extern "C" void seasons(int n,int days,const float* input,const float* mean,
                          const int32_t* calendar,int persistence,float amplitude_gate,
                          float* output) {
  const float nan=std::numeric_limits<float>::quiet_NaN();
  #pragma omp parallel for schedule(dynamic,32)
  for(int c=0;c<n;++c) {
    const float* m=mean+static_cast<size_t>(c)*366;
    const float* a=input+static_cast<size_t>(c)*days;
    float* o=output+static_cast<size_t>(c)*11;
    std::fill(o,o+11,nan);o[10]=2;
    bool ok=true;for(int d=0;d<366;++d)if(!std::isfinite(m[d]))ok=false;
    if(!ok)continue;
    int cool=std::min_element(m,m+366)-m,peak=std::max_element(m,m+366)-m;
    o[0]=m[peak]-m[cool];o[1]=(m[peak]+m[cool])/2;
    if(o[0]<amplitude_gate){o[10]=1;continue;}
    int bo=-1,be=-1,hot=0,cold=0,cycles=0;bool warm=false;
    for(int d=0;d<366;++d) {
      float v=m[(cool+d)%366];hot=v>o[1]?hot+1:0;cold=v<o[1]?cold+1:0;
      if(hot==persistence&&!warm){++cycles;warm=true;if(bo<0)bo=d-persistence+1;}
      if(cold==persistence&&warm){warm=false;if(be<0)be=d-persistence+1;}
    }
    if(cycles!=1||bo<0||be<bo){o[10]=3;continue;}
    int baseyear=cool<peak?1:0;
    int s=calendar[baseyear*366+cool];
    int stop=calendar[(baseyear+1)*366+cool];
    auto mapped=[&](int offset){int z=cool+offset;return calendar[(baseyear+z/366)*366+z%366];};
    int expected_onset=mapped(bo),expected_end=mapped(be);
    o[2]=(cool+bo)%366;o[3]=(cool+be)%366;
    int end=std::min(stop,days),begin=std::max(s,0);
    o[7]=o[8]=0;o[9]=std::max(0,end-begin);
    int onset=-1,finish=-1,first_missing=-1;hot=cold=cycles=0;warm=false;
    for(int t=begin;t<end;++t) {
      if(!std::isfinite(a[t])){if(first_missing<0)first_missing=t;hot=cold=0;continue;}
      ++o[8];o[7]+=a[t]>o[1];
      hot=a[t]>o[1]?hot+1:0;cold=a[t]<o[1]?cold+1:0;
      if(hot==persistence&&!warm){warm=true;++cycles;if(onset<0)onset=t-persistence+1;}
      if(cold==persistence&&warm){warm=false;if(finish<0)finish=t-persistence+1;}
    }
    if(s<0||(first_missing>=0&&(onset<0||first_missing<onset+persistence))){o[10]=5;continue;}
    if(onset<0){o[10]=4;continue;}
    if(cycles>1){o[10]=7;continue;}
    int delta=onset-expected_onset;
    int cycle_days=stop-s;
    while(delta>cycle_days/2)delta-=cycle_days;
    while(delta<-cycle_days/2)delta+=cycle_days;
    o[4]=delta;
    if(first_missing>=0&&(finish<0||first_missing<finish+persistence)){o[10]=5;o[4]=nan;continue;}
    if(finish<0){o[10]=6;continue;}
    o[5]=finish-onset;o[6]=o[5]-(expected_end-expected_onset);o[10]=0;
  }
}
