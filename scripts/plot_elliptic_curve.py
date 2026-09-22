"""绘制椭圆曲线 y^2 + xy = x^3 + a*x + b（实数域）。

系数极大（a ~ 2e62, b ~ 1.15e99），直接绘制会失真。
做加权尺度变换：x = c*X, y = c^(3/2)*Y，其中 c = b^(1/3)，
方程化为 Y^2 + c^(-1/2)*X*Y = X^3 + (a/c^2)*X + 1。
脚本同时输出归一化坐标图和原始坐标图。
"""

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "PingFang SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

a = -201769035260418549083594900060734240952308696994802735114305555
b = 1151107939141058565733479426024323225135665982951300586808823640527729578307228357301072889377

c = float(b) ** (1.0 / 3.0)  # x 的尺度因子
p = c ** -0.5  # 归一化后 xy 项系数
a_norm = float(a) / c**2  # 归一化后 x 项系数

X = np.linspace(-2.0, 2.5, 6000)
# 判别式：(pX)^2 + 4*(X^3 + a_norm*X + 1)
disc = (p * X) ** 2 + 4.0 * (X**3 + a_norm * X + 1.0)
mask = disc >= 0
Xv, dv = X[mask], np.sqrt(disc[mask])
Y1 = (-p * Xv + dv) / 2.0
Y2 = (-p * Xv - dv) / 2.0

fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(Xv, Y1, "b-", lw=1.5)
ax.plot(Xv, Y2, "b-", lw=1.5)
ax.axhline(0, color="gray", lw=0.5)
ax.axvline(0, color="gray", lw=0.5)
ax.grid(alpha=0.3)
ax.set_xlabel("X = x / $b^{1/3}$")
ax.set_ylabel("Y = y / $b^{1/2}$")
ax.set_title("$y^2 + xy = x^3 + ax + b$（实数域，归一化坐标）\n"
             f"$a={a}$,\n$b={b}$", fontsize=9)
fig.tight_layout()
out = "temp/elliptic_curve.png"
fig.savefig(out, dpi=150)
print("saved:", out)

# ---------- 原始坐标尺度 ----------
# 直接求解 y = (-x ± sqrt(x^2 + 4*(x^3 + a*x + b))) / 2
af, bf = float(a), float(b)
x = c * X  # 复用同一网格，换算回原坐标
f = x**3 + af * x + bf
disc_raw = x**2 + 4.0 * f
mask_raw = disc_raw >= 0
xv, dvr = x[mask_raw], np.sqrt(disc_raw[mask_raw])
y1 = (-xv + dvr) / 2.0
y2 = (-xv - dvr) / 2.0

fig2, ax2 = plt.subplots(figsize=(9, 6))
ax2.plot(xv, y1, "b-", lw=1.5)
ax2.plot(xv, y2, "b-", lw=1.5)
ax2.axhline(0, color="gray", lw=0.5)
ax2.axvline(0, color="gray", lw=0.5)
ax2.grid(alpha=0.3)
ax2.ticklabel_format(style="sci", scilimits=(0, 0))
ax2.yaxis.get_offset_text().set_fontsize(9)
ax2.xaxis.get_offset_text().set_fontsize(9)
ax2.set_xlabel("x")
ax2.set_ylabel("y")
ax2.set_title("$y^2 + xy = x^3 + ax + b$（实数域，原始坐标）\n"
              f"$a={a}$,\n$b={b}$", fontsize=9)
fig2.tight_layout()
out2 = "temp/elliptic_curve_raw.png"
fig2.savefig(out2, dpi=150)
print("saved:", out2)

# ---------- witness 点（来自 elliptic-rank.icarm.cloud/curve/273） ----------
from fractions import Fraction

WITNESS = [
    ("-4761204159891138283979053265906", "44764265461782973805868732003346421827415264953"),
    ("-14158422539541566469588779426546", "34199834254251713784176619895082644508395077433"),
    ("-11522667358396562420423130332066", "-44115070023357103726405378140637465204943359607"),
    ("-204839531927226269712122049566", "-34531574232452693997231136031282772551453427107"),
    ("3899324051227528532535432912094", "20582352852872417675268569815574934013539218953"),
    ("149851368287976334870008075289384", "-1826442728148288630645637436047625928557963231657"),
    ("240440240734591134232325971191694", "3721941824016160691689265341458606456425791434553"),
    ("58446054919170749975942104376446/9", "-289145377197241504032247540119122580900747897469/27"),
    ("25642661602146479458845459929344", "-113306861325798987289137854129016658652160209297"),
    ("25720885078613923889202869994094", "-113918565504468051036791617945007239588074855047"),
    ("4956414590296956229584100339596814", "348939117745197814060339374812186839746231405619513"),
    ("725964821994104294477684670330094", "-19556488133953913131900670560396205869420775943047"),
    ("20802191136944676997135829374", "33866070189878993817062821320678356972094522793"),
    ("79052318332408565020526148386446/9", "-202982221452031541387733280916787231176177841869/27"),
    ("-11232245340662775388535509780886", "-44725045659073489550941507272219743508825024527"),
    ("8362456338772815315335239525614", "-6972475614865802969141741730862843401376795527"),
    ("2011658715643038193607509024534", "27447371869432010931671648582500375378543228993"),
    ("5027695440284894460797358334207726/529", "-116678851641395817353208818767411586490893208148849/12167"),
    ("24649144267565165528439068441554", "105612540318783792474731275264940719325335867213"),
    ("-12211389420609043025008816968566", "42356225616159991618318584560811156010370207173"),
    ("7798692390172953821075781106768126/1369", "-691870045568822811690292896396241871567834072004011/50653"),
    ("87157992815740534253438806045216/9", "277139378791840529410298740802253693668472375061/27"),
    ("30786757706172245427369935940751/4", "58841476683002984849182029306774218124047405249/8"),
    ("245309280348041323814668746104926/25", "1346501028820415725958868015485008289981037919061/125"),
    ("-343878076324392159036619356326", "-34934957027779219869199839566344035316624147307"),
    ("544211807917340289404451270094", "-32271721754226832038590040491036826507284103047"),
    ("20286216384652039303944170492166526/9409", "-24593234902246769413006506020777691495865223432164871/912673"),
    ("-25558163204018019740775243468600589874/1760929", "74707049582033426178338768659390679551818201954095350999/2336752783"),
    ("4546264873863829383537112534021848799606/398521369", "-145386763829319577901520209264368135012688669041886277075149/7955682089347"),
    ("1709164065046406773620054102684586/169", "26450264171408287955631955124255640794301463854841/2197"),
]

# 精确验证：y^2 + x*y == x^3 + a*x + b（分数算术，零误差）
pts = [(Fraction(xs), Fraction(ys)) for xs, ys in WITNESS]
on_curve = all(py * py + px * py == px**3 + a * px + b for px, py in pts)
print(f"witness points on curve (exact check): {on_curve}  ({len(pts)} points)")

wx = np.array([float(px) for px, _ in pts])
wy = np.array([float(py) for _, py in pts])

# ---------- 原始坐标 + witness 点（全景 + 鼻尖局部放大） ----------
# 全景网格需覆盖最远的点 x ≈ 4.96e33（归一化 X ≈ 473）
Xg = np.concatenate([np.linspace(-1.6, 3.0, 8000), np.linspace(3.0, 500.0, 6000)])
xg = c * Xg
fg = xg**3 + af * xg + bf
dg = xg**2 + 4.0 * fg
mg = dg >= 0
xg, dg = xg[mg], np.sqrt(dg[mg])
yg1 = (-xg + dg) / 2.0
yg2 = (-xg - dg) / 2.0

fig3, ax3 = plt.subplots(figsize=(10, 7))
ax3.plot(xg, yg1, "b-", lw=1.2)
ax3.plot(xg, yg2, "b-", lw=1.2)
ax3.axhline(0, color="gray", lw=0.5)
ax3.axvline(0, color="gray", lw=0.5)
ax3.grid(alpha=0.3)
ax3.ticklabel_format(style="sci", scilimits=(0, 0))
ax3.set_xlabel("x")
ax3.set_ylabel("y")
ax3.set_title("$y^2 + xy = x^3 + ax + b$ — curve #273, rank ≥ 30（原始坐标）", fontsize=10)

# 内嵌放大：鼻尖附近 [-2e31, 3e31]，标注范围内的 witness 点
axin = ax3.inset_axes([0.13, 0.42, 0.42, 0.5])
axin.plot(xv, y1, "b-", lw=1.0)
axin.plot(xv, y2, "b-", lw=1.0)
in_m = (wx > -2e31) & (wx < 3e31)
axin.scatter(wx[in_m], wy[in_m], c="red", s=18, zorder=5,
             label=f"witness 点（{int(in_m.sum())} 个在此范围）")
axin.legend(loc="lower right", fontsize=7)
axin.set_xlim(-2e31, 3e31)
axin.set_ylim(-1.5e47, 1.5e47)
axin.grid(alpha=0.3)
axin.ticklabel_format(style="sci", scilimits=(0, 0))
axin.tick_params(labelsize=7)
axin.set_title("鼻尖附近放大", fontsize=8)
ax3.indicate_inset_zoom(axin, edgecolor="gray", alpha=0.5)

fig3.tight_layout()
out3 = "temp/elliptic_curve_raw_points.png"
fig3.savefig(out3, dpi=150)
print("saved:", out3)

# ---------- 归一化坐标 + witness 点（同版式） ----------
# 归一化方程：Y^2 + p*X*Y = X^3 + a_norm*X + 1
c32 = c ** 1.5
Xw, Yw = wx / c, wy / c32

discg = (p * Xg) ** 2 + 4.0 * (Xg**3 + a_norm * Xg + 1.0)
mgn = discg >= 0
Xgn, dgn = Xg[mgn], np.sqrt(discg[mgn])
Yg1 = (-p * Xgn + dgn) / 2.0
Yg2 = (-p * Xgn - dgn) / 2.0

fig4, ax4 = plt.subplots(figsize=(10, 7))
ax4.plot(Xgn, Yg1, "b-", lw=1.2)
ax4.plot(Xgn, Yg2, "b-", lw=1.2)
ax4.axhline(0, color="gray", lw=0.5)
ax4.axvline(0, color="gray", lw=0.5)
ax4.grid(alpha=0.3)
ax4.set_xlabel("X = x / $b^{1/3}$")
ax4.set_ylabel("Y = y / $b^{1/2}$")
ax4.set_title("$y^2 + xy = x^3 + ax + b$ — curve #273, rank ≥ 30（归一化坐标）", fontsize=10)

axin4 = ax4.inset_axes([0.13, 0.42, 0.42, 0.5])
axin4.plot(Xv, Y1, "b-", lw=1.0)
axin4.plot(Xv, Y2, "b-", lw=1.0)
in_mn = (Xw > -2.0) & (Xw < 3.0)
axin4.scatter(Xw[in_mn], Yw[in_mn], c="red", s=18, zorder=5,
              label=f"witness 点（{int(in_mn.sum())} 个在此范围）")
axin4.legend(loc="lower right", fontsize=7)
axin4.set_xlim(-2.0, 3.0)
axin4.set_ylim(-1.5, 1.5)
axin4.grid(alpha=0.3)
axin4.tick_params(labelsize=7)
axin4.set_title("鼻尖附近放大", fontsize=8)
ax4.indicate_inset_zoom(axin4, edgecolor="gray", alpha=0.5)

fig4.tight_layout()
out4 = "temp/elliptic_curve_norm_points.png"
fig4.savefig(out4, dpi=150)
print("saved:", out4)
print(f"witness x range: [{wx.min():.3e}, {wx.max():.3e}],  y range: [{wy.min():.3e}, {wy.max():.3e}]")
print(f"c = b^(1/3) = {c:.6e},  p = c^(-1/2) = {p:.3e},  a/c^2 = {a_norm:.3e}")
