W=type
V=max
U=str
P=int
N=open
M=list
L=Exception
J=len
I=range
B=format
import argparse as h,base64 as X,zlib as Y,csv,datetime as C,gzip,io,json as K,os as G,re as D,sys,time as E,zipfile as i,base64 as j,zlib as k,functools as l
@l.lru_cache(None)
def A(x):return k.decompress(j.b85decode(x)).decode()
try:import requests as Q
except ImportError:sys.exit(A('c-nh8r{Tr2Muno(!qU{@lH&J!W))->C}idpmn7!oz=Z*MdJ*y'))
m=A('c-r&Lugc8HNz^yhGf>b7&&*57FE3W`3sEpM&@-@B01B9ySSwVRnP@6F78K;9hNmWZXO`%j8k_4Gn<;2`dxZG<=qTi5W~VB+rzU6TYbrQr6y@ip>KhuF0Zj}}OiL`vgenIBr`;a!')
H='d'
R=G.path.join(H,A('c-kx0OGzvN00mwF+W'))
Z=Q.Session()
Z.headers.update({A('c-jjsPA$@POi#@#0RR*m1H1'):m,A('c-nJJPEIW-(e+8pOD|1KPXz!gzy+c'):A('c-pJV&<zRKsmib}v^CJP1OOuh1W5')})
a=[]
def F(v30_):a.append(v30_)
def O(v31_,**B):
	C=None
	for G in I(3):
		try:F=Z.get(v31_,timeout=B.pop(A('c-kw;%uUTNEdc-w2?Gc'),60),**B);F.raise_for_status();return F
		except Q.exceptions.SSLError as D:C=D;B[A('c-kvVEy_%*1ON#O0+s')]=False;Q.packages.urllib3.disable_warnings()
		except L as D:C=D;E.sleep(3*(G+1))
	raise C
def b(v33_,v34_,v35_):
	B=v33_
	if not v35_:return
	G.makedirs(G.path.dirname(B),exist_ok=True);D=not G.path.exists(B)
	with N(B,'a',newline='',encoding=A('c-kv1Nz=6e00rU!wE'))as E:
		C=csv.writer(E)
		if D:C.writerow(v34_)
		C.writerows(v35_)
def S(v36_,v37_,v38_):
	G.makedirs(G.path.dirname(v36_),exist_ok=True)
	with N(v36_,'w',newline='',encoding=A('c-kv1Nz=6e00rU!wE'))as C:B=csv.writer(C);B.writerow(v37_);B.writerows(v38_)
n=D.compile(A('c-nh5W!sBQyK8{><-*>Y7t8vgyyt!GH7{0lfOs!k*Su_>So3tjMj)%^*_3Th`={w?!PHGzp{Mn1#mr~Brh%k@B2VY<0&$);?|imk4*))<K-B'))
c=D.compile(A('c-nh0Vehl)OKV;>_C4FN@Y$UC2-eGKlWU%CY<sqQf6a?MQ=V?<1Ia$$zVgMwxggfFX?tHR>;dWpah^8LdA4@Z%f^+@r>v-X(Y{Kr+Caz9sP^g3Eg+Uz?Xx)@P{#D78ZWkPhw9b@0NHC!*#'))
def d(v39_):
	C=v39_;C=D.sub(A('c-o6`0RRC00HF'),'',U(C or''))
	if J(C)==8:return''.join([B(C[:4],''),A('c-qqi001rkE&'),B(C[4:6],''),A('c-qqi001rkE&'),B(C[6:],'')])
	return''
def o(v40_,v41_):
	Q=v40_.setdefault('1',{})
	if Q.get(A('c-l+J&r6L@ECB!uY69B'))and(C.datetime.now()-C.datetime.fromisoformat(Q[A('c-l+J&r6L@ECB!uY69B')])).days<7:F(A('c-o83Ni2_5FjsiGWaZP=<xjV7dNzB@vuPV%Huk;W)AM5cW*`FqV+R%A'));return
	h=C.date.today();R,L,T,Y=[],[],[],[]
	for(I,Z)in[(A('c-nimdFs=B-2e~s1YH'),A('c-qS-DJdwn($~*PEZ57;&(cfJFVib2*H0|S)OXI%_em_*_X_s+0{{sp4Hf')),(A('c-nh9aqpAeO8^h^1a|'),A('c-qS-DJdwn($~*PEZ57;&(cfJFVib2*H0|S)OXI%_b*CGEz<W2_V)t-CJznn'))]:
		F(''.join([A('c-o83Ni2_5c(SAW#hy+D04o~?kp'),B(I,''),A('c-nivXBGei;sQn'),B(Z,'')]));j=O(Z,timeout=300);M=j.content
		if M[:2]==b'PK':a=i.ZipFile(io.BytesIO(M));E=[B for B in a.namelist()if B.lower().endswith(A('c-qs;D$dUX00lS!=>'))][0];M=a.read(E)
		U=K.loads(M.decode(A('c-kv1Nz=8^EzV2_01x~FB>')));b=U.get(A('c-r$xEH4HC1GoX0'))or U.get(A('c-qTJEH4HC1ULb>'))or[];F(''.join([A('c-o83Ni2_5000OF0v!'),B(I,''),A('c-m6{001EXAp'),B(J(b),''),A('c-jFJ0PFuC>4T{6yo~6xhvt@<=9i`BoSz_yvke9'),B(U.get(A('c-jjsNJ%V7bpc`k6+{E#')),'')]))
		for D in b:
			E=D.get(A('c-r$xEcZ*yO$7i7P6DO'),'');G=d(D.get(A('c-r$xEceY%$xO>kO>s#qNd*8cw*|x')));N=(D.get(A('c-r$xEO$&w%uC77^UE(u1pp^~1#S'))or'').strip();W=D.get(A('c-r$xEO#s_$xO~kEd~G?Km=R'))or[];P=D.get(A('c-r$xEDsIx0RRVn0vG'),'');R.append([I,D.get(A('c-r$xEcZz*OU(fQ4S@q4'),''),E,D.get(A('c-r$xEO$;UNlni$sssQS{sdz'),''),G,d(D.get(A('c-r$xEO$*yOHD4xEK7AsEJ+0bGt~w('))),N,J(W),P])
			if n.search(E)and not N:
				e=''
				if G:e=round((h-C.date.fromisoformat(G)).days/365.25,1)
				L.append([e,G,E,D.get(A('c-r$xEO$;UNlni$sssQS{sdz'),''),I,P])
			for f in W:
				X=(f.get(A('c-nI;D#=XFNp;T8D@n~O0RSlv1)u'))or'').replace('\r','').replace('\n',' ')
				if not N and c.search(X):g=c.search(X);k=V(0,g.start()-60);T.append([E,f.get(A('c-nI;D#=XFN%hMI01;gSf&'),''),G,X[k:g.end()+80],P])
			Y.append({A('c-qU(%u4|P1S<ij'):I,A('c-qTL%uNLV1RepR'):E,A('c-l)&EJ;nzFRBCp4!#3l'):D.get(A('c-r$xEO$;UNlni$sssQS{sdz')),A('c-qU&PsvQnOicj*4&MVp'):G,A('c-l)$O3X{i&jSDp4+7K'):N,A('c-kv1$^ifZvH?^'):P,A('c-qUzEH23}%1kW=024t2+W'):D.get(A('c-r$xEceJPF3B&-Of3cg9)$$o')),A('c-l)WD#=XFNi7Bd4*&yL'):[[B.get(A('c-nI;D#=XFN%hMI01;gSf&'),''),B.get(A('c-nI;D#=XFNp;T8D@n~O0RSlv1)u'),'')]for B in W]})
	L.sort(key=lambda x:(x[0]=='',-(x[0]or 0)));S(''.join([B(H,''),A('c-qrX)Hl#eE-nKA32p*v')]),['k','v','n','g','m','e','x','c','u'],R);S(''.join([B(H,''),A('c-qrX)Hl>iE-nKA33CE#')]),['y','m','n','g','k','u'],L);S(''.join([B(H,''),A('c-qrX)Hl*gE-nKA33vi*')]),['n','a','m','t','u'],T)
	with gzip.open(''.join([B(H,''),A('c-qrX)Hl{kuL1xE9|8g')]),A('c-kv30RRDH0PF'),encoding=A('c-kv1Nz=6e00rU!wE'))as l:
		for m in Y:l.write(K.dumps(m,ensure_ascii=False)+'\n')
	Q[A('c-l+J&r6L@ECB!uY69B')]=C.datetime.now().isoformat(timespec=A('c-kvYP0r6tDFy%wx&rV'));F(''.join([A('c-o83Ni2_5c)G6VS;vI;duBb~vG>Ko6$${1Mhz?'),B(J(R),''),A('c-nj1(D-c1wilarzgW0J0RTW92)h'),B(J(L),''),A('c-jFL0O|kZfPv<jg6Wo%=%|Y5nV;sOo#vK@Agr_wdH'),B(J(T),'')]))
p=A('c-qS-DJdwn($_CYPS#B<$kfX(NX<(t&C^RPD9{J;^>Z?dOOh&65=&C;L4<8}EdbaD65s')
e=C.date(2012,7,1)
def q(v42_,v43_):
	D=v42_.setdefault('2',{});J=C.date.fromisoformat(D[A('c-qTLEl({j0RRa20+#')])if D.get(A('c-qTLEl({j0RRa20+#'))else None;K=C.date.fromisoformat(D[A('c-qU)Nl7g(0RRZq0*n')])if D.get(A('c-qU)Nl7g(0RRZq0*n'))else None;Q=C.date.today();M=[]
	if J is None:R=Q-C.timedelta(days=1);M=[R-C.timedelta(days=A)for A in I(0,100000)if R-C.timedelta(days=A)>=e]
	else:M=[J+C.timedelta(days=A)for A in I(1,(Q-J).days)];M+=[K-C.timedelta(days=A)for A in I(1,(K-e).days+1)]
	S=0
	for G in M:
		if E.time()>v43_:break
		try:X=O(p.format(G.strftime(A('c-m8qRLxaQ0RROm0h#'))));Y=X.json().get(A('c-kvUP0lY$DFy%wzXJ0'))or[]
		except L as T:
			F(''.join([A('c-o6DNKTGb000N)0uK'),B(G,''),A('c-m8Vx@6<Csng%@nFRnM)&{Z'),B(W(T).__name__,''),A('c-pg40001%09y'),B(U(T)[:120],'')]));D[A('c-l)XD#|Y^1^@{P0-g')]=D.get(A('c-l)XD#|Y^1^@{P0-g'),0)+1
			if D[A('c-l)XD#|Y^1^@{P0-g')]>20:F(A('c-jFc0NDRqaARX#AnAak=emsPjIZdbq~)Zl<)oVLyo~99ndYpa<%Njlft=p}8CU'));break
			continue
		V=[]
		for N in Y:P=N.get(A('c-l)U%1liI00trg2>'))or{};Z=P.get(A('c-l+O&n-yI%S<f>01~VNzy'))or{};V.append([G.isoformat(),P.get(A('c-kweEJy_a1cU*@'),''),P.get(A('c-kw;EXhd)00xEvBL'),''),P.get(A('c-l)&EJ;nzFRBCp4!#3l'),''),N.get(A('c-kw?%Pfh{OUz9L023ku!2'),''),'|'.join(Z.get(A('c-qTL%uOu@00uJx6#'))or[]),N.get(A('c-kv1$^ifZvH?^'),''),N.get(A('c-kvT%}Yrwicc)aj4v(90RSsz1<n'),'')])
		b(''.join([B(H,''),A('c-qrX(gy$mg8;z'),B(G.strftime(A('c-m8qRLund0$KqP')),''),A('c-qrTE-nKA13>|M')]),['d','t','n','g','o','c','u','i'],V)
		if J is None or G>J:J=G
		if K is None or G<K:K=G
		D[A('c-qTLEl({j0RRa20+#')],D[A('c-qU)Nl7g(0RRZq0*n')]=J.isoformat(),K.isoformat();S+=1;E.sleep(.8)
	F(''.join([A('c-o6DNKTGbcs6Ivvo#A}ES~dZSDOL=WjqSo'),B(S,''),A('c-jFJ0PFuC<)o?ayqo8nuH}i1=C-xylZzmZ3=KN'),B(D.get(A('c-qU)Nl7g(0RRZq0*n')),''),A('c-m8_Qvd(~e*nJ'),B(D.get(A('c-qTLEl({j0RRa20+#')),'')]))
f=[A('c-r&HOiRry&dtwDtporXA_Rp'),A('c-qUz&rQ`WPRvOK01=M^d;'),A('c-l+VEzZa<D9Fr92LKfb1N#'),A('c-l)&ECK)mU;#G'),A('c-r&KD=sZc%u7xM01_YrsQ'),A('c-nJHOse$FFUd$P0ss`F1MU'),A('c-jjnP0Gnk4o)p9OUwfR9<>C|'),A('c-jk2%t<V&1ONyP0&M'),A('c-r$Q&df{BC<Oot<O0('),A('c-jj|P0on-%1;6S4POHP'),A('c-nKyFD{Pv$xKTH01+VrcK'),A('c-jljPb-P{%1;6S4eJ9J'),A('c-nJJPR=jQE6L1D2LKgf1Pl'),A('c-jj|tN;K4IRP#'),A('c-r$xEU!#00ssg$0(A'),A('c-jj}%`1s7Nz4ZT4m<-r'),A('c-r&LPs+?m4M?m601-6<g8'),A('c-jjt$xqG(00r^_1p')]
r=D.compile(A('c-pf`$t+Vy&PgmTwpA+9P0cG&veVGhve&dh63<O6%2u)i03v@4Vg'),D.S)
s=D.compile(A('c-pf`$t+Vy&PgmTwpGe2N=;U>)3CR)DK1FNi;lC4)w0vH*NBd@iPh2s02$y6od'))
t=D.compile(A('c-pf`RLCewO|w<f&`(M#){l-;iq+QljnUJHNzvAf(F5}}mFzV1wCpu)^b_p>NKFik'),D.S)
u=D.compile(A('c-qS-N=>s>(oae%){l<UkJZ-C%u7kF(1=OV){N21D9O!HvWt$hiPd_tqwD2@MgU}s5ZC'))
def v(v44_):
	B=v44_;B=B.strip()
	if B==A('c-nj3(FOnnP674'):return 100
	if B.startswith('X'):return-10 if B==A('c-o7I0003B0I>')else-P(B[1:]or 1)*10
	return P(B)if B.isdigit()else 0
def w(v45_,v46_):
	F=O(''.join([A('c-qS-DJdwn($_C9FV`z5DbY(#)=x?*)&~G)mIy!'),B(v45_,''),A('c-qs?%u7kF000M50!R'),B(v46_,''),A('c-qs;D9OzM00k`p<N')]),cookies={A('c-qS^OD!_A000Pb0ww'):'1'});G=[]
	for H in r.findall(F.text):
		E=t.search(H)
		if not E:continue
		I=P(E.group(2));G.append([C.datetime.fromtimestamp(I).strftime(A('c-m8q)K$&ZRZUS)^{`U)1ppW211$')),v((s.search(H)or[None,''])[1]),D.sub(A('c-o68)&>9qC;<B'),' ',E.group(3)).strip(),A('c-qS-DJdwn($_C9FV`z5DbY(#1^_^j2CD')+E.group(1)])
	return F.text,G
def x(v47_,v48_):
	R=v48_;a=v47_.setdefault('3',{});T=f;c=V(6e1,(R-E.time())/V(1,J(T)))
	for G in T:
		if E.time()>R:break
		C=a.setdefault(G,{})
		if C.get(A('c-l)zO-um*1L*;e')):continue
		d=min(R,E.time()+c)
		try:e=O(''.join([A('c-qS-DJdwn($_C9FV`z5DbY(#)=x?*)&~G)mIy!'),B(G,''),A('c-qs?%u7kF(90;v%>e)x;{+=')]),cookies={A('c-qS^OD!_A000Pb0ww'):'1'})
		except L as g:
			C[A('c-l)XD#|Y^1^@{P0-g')]=C.get(A('c-l)XD#|Y^1^@{P0-g'),0)+1
			if C[A('c-l)XD#|Y^1^@{P0-g')]>=3:C[A('c-l)zO-um*1L*;e')]=True
			F(''.join([A('c-o6DC@G0m000PH0x<'),B(G,''),A('c-m8V);amfj^3Bky5H}a1pqlD2%7'),B(W(g).__name__,''),A('c-nivr{npS^)FU*C;$K`_y)E'),B(C[A('c-l)XD#|Y^1^@{P0-g')],''),A('c-m8Vwr1h`J)Hm$`2>g')]));continue
		U=u.search(e.text);S=P(U.group(1))+1 if U else 1;D,K=C.get(A('c-qUzOwRxS1Qh|H')),C.get(A('c-qU!F9!euoB>k'));Q=[]
		if D is None:Q=M(I(S-1,0,-1))
		else:Q=M(I(D+1,S));Q+=M(I(K-1,0,-1))
		X=0
		for N in Q:
			if E.time()>d:break
			try:k,h=w(G,N)
			except L:continue
			Y={}
			for Z in h:Y.setdefault(Z[0][:4],[]).append(Z)
			for(i,j)in Y.items():b(''.join([B(H,''),A('c-qrX)&~Fqg#f|'),B(f.index(G),''),A('c-qqk001xmFa'),B(i,''),A('c-qrTE-nKA13>|M')]),['t','p','n','u'],j)
			D=N if D is None or N>D else D;K=N if K is None or N<K else K;C[A('c-qUzOwRxS1Qh|H')],C[A('c-qU!F9!euoB>k')]=D,K;X+=1;E.sleep(.5)
		F(''.join([A('c-o6DC@G0m000PH0x<'),B(G,''),A('c-nivXV$YhYo4uHr~m*d7zW1'),B(X,''),A('c-m8VxuEg=p4m^gZ+f<E>x;?V3YmE+sTBaEqYX{'),B(C.get(A('c-qU!F9!euoB>k')),''),A('c-pH2004gge*'),B(C.get(A('c-qUzOwRxS1Qh|H')),''),A('c-nivr{me2hG)|@C;$K_hz5c'),B(S,''),A('c-nivrxO4K(E>F')])+(A('c-nivch1x8n_euQ^R#2b%W2)uJ39b>nGD?')if C.get(A('c-qU!F9!euoB>k'))==1 else''))
def g(v49_):
	B=K.dumps(v49_,ensure_ascii=False,separators=(',',':')).encode(A('c-kv1Nz=6e00rU!wE'))
	with N(R,A('c-kvZ0ssM00NM'))as C:C.write(X.b85encode(Y.compress(B,9)))
T={'1':o,'2':q,'3':x}
y={'1':.15,'2':.35,'3':.5}
def z():
	O=h.ArgumentParser();O.add_argument(A('c-qq~0002Y0G<'),dest=A('c-kv81ONdQ0HX'),choices=M(T));O.add_argument(A('c-qq~0RRBd0HO'),dest=A('c-kv80ssLP0Hg'),type=float,default=45);I=O.parse_args();G.makedirs(H,exist_ok=True);D={}
	if G.path.exists(R):
		with N(R,A('c-kvU0ssL>0M!'))as Z:D=K.loads(Y.decompress(X.b85decode(Z.read())).decode(A('c-kv1Nz=6e00rU!wE')))
	Q=E.time();P=I.q2*60;b=[I.q1]if I.q1 else M(T)
	for J in b:
		c=1. if I.q1 else y[J];S=min(Q+P,E.time()+P*c)
		if J=='3':S=Q+P
		try:T[J](D,S)
		except L as V:F(''.join([A('c-o5w003M7Tm'),B(J,''),A('c-o6qc(Qx<)9#s1mu!4Cb^7}~vjAa^3vv'),B(W(V).__name__,''),A('c-pg40001%09y'),B(U(V)[:200],'')]))
		g(D)
	D[A('c-qTJEG~&JD$N4`4=)30')]=C.datetime.now().isoformat(timespec=A('c-kvYP0r6tDFy%wx&rV'));D[A('c-qTJEG~)9$xjCW4+;ZT')]=a[-40:];g(D)
if __name__==A('c-o7P&rQtCi;o8Y4i^I='):z()