from math import cos,pi,sqrt,ceil
from kandinsky import set_pixel
z=range;w=round;nc=isinstance
def ch(l,e):
 t=[];j=0
 for i in z(len(l)):
  for _ in z(l[i]):fl(t,e[j],i);j+=1
 return t
def fl(r,e,p):
 if nc(r,list):
  if p==0:
   if len(r)<2:r.append(e);return 1
   return 0
  for i in [0,1]:
   if len(r)==i:r.append([])
   if fl(r[i],e,p-1):return 1
 return 0
def bi(d):
 r=0
 for b in d:r=(r<<8)|b
 return r
def db(c,b):l=2**(c-1);return b if b>=l else b-(l*2-1)
def yr(y,c,s):r=y+1.402*(s-128);g=y-0.34414*(c-128)-0.714136*(s-128);b=y+1.772*(c-128);return(max(0,min(255,w(r))),max(0,min(255,w(g))),max(0,min(255,w(b))))
class J:
 def __init__(s,b):s.b=b;s.p=0;s.c={};s.ht={};s.q={};s.s=[0,0];s.w=s.h=0;s.i=[];s.rm()
 def rm(s):
  while 1:
   m=s.r(2)
   if m==65496:...
   elif m==65497:break
   elif m==65476:s.dh()
   elif m==65499:s.dq()
   elif m==65472:s.fh()
   elif m==65498:s.sh();s.sc()
   else:s.k(s.r(2,k=1))
   if s.p//8>=len(s.b):break
 def dh(s):
  s.k(2);t=s.r();l=[s.r()for _ in z(16)];e=[]
  for b in l:e+=[s.r()for _ in z(b)]
  s.ht[t]=ch(l,e)
 def dq(s):s.k(2);t=s.r();s.q[t]=s.r(64,1)
 def fh(s):
  s.k(3);s.h=s.r(2);s.w=s.r(2);n=s.r()
  for _ in z(n):c=s.r();s.s[0]=max(s.s[0],s.r(k=1)>>4);s.s[1]=max(s.s[1],s.r()&15);s.c[c]={0:s.r()}
 def sh(s):
  s.k(2);n=s.r()
  for _ in z(n):c=s.r();s.c[c][1]=s.r(k=1)>>4;s.c[c][2]=s.r()&15
  s.k(3)
 def sc(s):
  s.i=[[cos((pi/8)*(p+0.5)*n)*(1/sqrt(2)if n==0 else 1)for n in z(8)]for p in z(8)];yc=bc=rc=0;sp=s.s[0]*s.s[1]
  for y in z(ceil(s.h/(8*s.s[1]))):
   for x in z(ceil(s.w/(8*s.s[0]))):
    ym=[]
    for _ in z(sp):yt,yc=s.bm(s.c[1],yc);ym.append(yt)
    bm,bc=s.bm(s.c[2],bc);rm,rc=s.bm(s.c[3],rc);s.dp(x,y,ym,bm,rm)
 def dp(s,x,y,ym,bm,rm):
  bw=8*s.s[0];bh=8*s.s[1]
  for i in z(len(ym)):
   ix=i%s.s[0];iy=i//s.s[0]
   for yy in z(8):
    by=iy*8+yy;py=y*bh+by
    if py>=s.h:break 
    for xx in z(8):
     bx=ix*8+xx;px=x*bw+bx
     if px>=s.w:break
     sx=bx//s.s[0];sy=by//s.s[1];c=yr(ym[i][xx][yy],bm[sx][sy],rm[sx][sy]);set_pixel(px,py,c)
 def bm(s,cp,dc):
  q=s.q[cp[0]];c=s.rc(s.ht[cp[1]]);b=s.rb(c);dc+=db(c,b);r=[0]*64;r[0]=dc*q[0];i=1;ht=s.ht[16+cp[2]]
  while i<64:
   c=s.rc(ht)
   if c==0:break
   i+=c>>4;c&=15
   if i>=64:break
   b=s.rb(c);r[i]=db(c,b)*q[i];i+=1
  return s.it(s.rf(r)),dc
 def it(s,l):
  o=[[0]*8 for _ in z(8)]
  for y in z(8):
   for x in z(8):
    ty=[s.i[y][u] for u in z(8)];tx=[s.i[x][p] for p in z(8)];c=0
    for u in z(8):
     g=u*8
     for p in z(8):c+=l[g+p]*ty[p]*tx[u]
    o[y][x]=w(c/4)+128
  return o
 def rf(s,c):
  l=[0,1,5,6,14,15,27,28,2,4,7,13,16,26,29,42,3,8,12,17,25,30,41,43,9,11,18,24,31,40,44,53,10,19,23,32,39,45,52,54,20,22,33,38,46,51,55,60,21,34,37,47,50,56,59,61,35,36,48,49,57,58,62,63]
  for i in z(64):l[i]=c[l[i]]
  return l
 def rc(s,h):
  r=h
  while nc(r,list):r=r[s.gb()]
  return r
 def r(s,n=1,t=0,k=0):
  p=s.p//8;d=s.b[p:p+n]
  if not k:s.p+=n*8
  return d if t else bi(d)
 def k(s,n):s.p+=n*8
 def gb(s):s.sf();o=s.b[s.p>>3];b=(o>>(7-s.p&7))&1;s.p+=1;return b
 def sf(s):
  if(s.p&7)==0:
   b=s.p>>3
   if s.b[b]==0 and s.b[b-1]==255:s.p+=8 
 def rb(s,n):
  r=0
  for _ in z(n):r=(r<<1)|s.gb()
  return r
def open(b):J(b)