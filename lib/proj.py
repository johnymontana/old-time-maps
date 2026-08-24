"""Projections and datums, hand-rolled as in the montana pipeline.

Everything a sheet needs to move between the scan, the earth and the grid:

    Lcc          Lambert conformal conic on the unit sphere — the grid every
                 sheet renders in (montana convention: X/Y are dimensionless,
                 multiply by R to get metres)
    polyconic    the American Polyconic on Clarke 1866, in metres — the
                 projection early USGS/Army quads are drawn and georeferenced in
    wgs84_to_nad27 / nad27_to_wgs84
                 abridged Molodensky, three-parameter CONUS values
    poly_basis   bivariate polynomial design matrix for georeferencing fits
"""
import math
import numpy as np

R_EARTH = 6371000.0

# --------------------------------------------------------------------- LCC
class Lcc:
    """Lambert conformal conic, unit sphere; same maths as montana/build.py."""
    def __init__(self, sp1, sp2, lon0):
        t = lambda phi: math.tan(math.pi/4 + phi/2)
        p1, p2 = math.radians(sp1), math.radians(sp2)
        if abs(sp1 - sp2) < 1e-9:
            self.n = math.sin(p1)
        else:
            self.n = math.log(math.cos(p1)/math.cos(p2)) / math.log(t(p2)/t(p1))
        self.f = math.cos(p1)*t(p1)**self.n / self.n
        self.lon0 = math.radians(lon0)
        self.sp1, self.sp2, self.lon0_deg = sp1, sp2, lon0

    def fwd(self, lon, lat):
        lon = np.radians(np.asarray(lon, float)); lat = np.radians(np.asarray(lat, float))
        rho = self.f/np.power(np.tan(np.pi/4 + lat/2), self.n)
        th  = self.n*(lon - self.lon0)
        return rho*np.sin(th), -rho*np.cos(th)

    def inv(self, X, Y):
        X = np.asarray(X, float); Y = np.asarray(Y, float)
        rho = np.hypot(X, Y); th = np.arctan2(X, -Y)
        return (np.degrees(self.lon0 + th/self.n),
                np.degrees(2*np.arctan(np.power(self.f/rho, 1.0/self.n)) - np.pi/2))

# --------------------------------------------------- polyconic (Clarke 1866)
CLARKE_A, CLARKE_INVF = 6378206.4, 294.9786982138982
WGS_A,    WGS_INVF    = 6378137.0, 298.257223563

def _marc(phi, a, e2):
    e4 = e2*e2; e6 = e4*e2
    return a*((1 - e2/4 - 3*e4/64 - 5*e6/256)*phi
              - (3*e2/8 + 3*e4/32 + 45*e6/1024)*np.sin(2*phi)
              + (15*e4/256 + 45*e6/1024)*np.sin(4*phi)
              - (35*e6/3072)*np.sin(6*phi))

def polyconic(lon, lat, lon0, lat0, a=CLARKE_A, invf=CLARKE_INVF):
    """Forward American Polyconic, metres. Vectorised; assumes lat well off 0."""
    f = 1.0/invf; e2 = 2*f - f*f
    phi = np.radians(np.asarray(lat, float))
    lam = np.radians(np.asarray(lon, float) - lon0)
    m0  = _marc(np.radians(lat0), a, e2)
    n   = a/np.sqrt(1 - e2*np.sin(phi)**2)
    ee  = lam*np.sin(phi)
    cot = 1.0/np.tan(phi)
    x = n*cot*np.sin(ee)
    y = _marc(phi, a, e2) - m0 + n*cot*(1 - np.cos(ee))
    return x, y

# ------------------------------------------------------ datum: NAD27 ↔ WGS84
def _molodensky(lon, lat, dx, dy, dz, a_src, invf_src, a_dst, invf_dst):
    f_src = 1.0/invf_src; f_dst = 1.0/invf_dst
    da, df = a_dst - a_src, f_dst - f_src
    e2 = 2*f_src - f_src*f_src
    phi = np.radians(np.asarray(lat, float)); lam = np.radians(np.asarray(lon, float))
    sp, cp = np.sin(phi), np.cos(phi)
    sl, cl = np.sin(lam), np.cos(lam)
    rn = a_src/np.sqrt(1 - e2*sp*sp)
    rm = a_src*(1 - e2)/np.power(1 - e2*sp*sp, 1.5)
    dphi = (-dx*sp*cl - dy*sp*sl + dz*cp + (a_src*df + f_src*da)*np.sin(2*phi)) / rm
    dlam = (-dx*sl + dy*cl) / (rn*cp)
    return np.degrees(lam + dlam), np.degrees(phi + dphi)

def nad27_to_wgs84(lon, lat):
    return _molodensky(lon, lat, -8.0, 160.0, 176.0, CLARKE_A, CLARKE_INVF, WGS_A, WGS_INVF)

def wgs84_to_nad27(lon, lat):
    return _molodensky(lon, lat, 8.0, -160.0, -176.0, WGS_A, WGS_INVF, CLARKE_A, CLARKE_INVF)

# --------------------------------------------- inverse transverse Mercator
GRS80_A, GRS80_INVF = 6378137.0, 298.257222101

def tm_inverse(E, N, lon0, k0=0.9996, fe=500000.0, fn=0.0,
               a=GRS80_A, invf=GRS80_INVF):
    """UTM-style eastings/northings (metres) → lon/lat degrees (Snyder)."""
    f = 1.0/invf; e2 = 2*f - f*f; ep2 = e2/(1-e2)
    E = np.asarray(E, float); N = np.asarray(N, float)
    m = (N - fn)/k0
    mu = m/(a*(1 - e2/4 - 3*e2*e2/64 - 5*e2**3/256))
    e1 = (1 - math.sqrt(1-e2))/(1 + math.sqrt(1-e2))
    phi1 = (mu + (3*e1/2 - 27*e1**3/32)*np.sin(2*mu)
               + (21*e1*e1/16 - 55*e1**4/32)*np.sin(4*mu)
               + (151*e1**3/96)*np.sin(6*mu)
               + (1097*e1**4/512)*np.sin(8*mu))
    sp, cp = np.sin(phi1), np.cos(phi1)
    c1 = ep2*cp*cp; t1 = np.tan(phi1)**2
    n1 = a/np.sqrt(1 - e2*sp*sp)
    r1 = a*(1-e2)/np.power(1 - e2*sp*sp, 1.5)
    d = (E - fe)/(n1*k0)
    phi = phi1 - (n1*np.tan(phi1)/r1)*(d*d/2
          - (5 + 3*t1 + 10*c1 - 4*c1*c1 - 9*ep2)*d**4/24
          + (61 + 90*t1 + 298*c1 + 45*t1*t1 - 252*ep2 - 3*c1*c1)*d**6/720)
    lam = (d - (1 + 2*t1 + c1)*d**3/6
             + (5 - 2*c1 + 28*t1 - 3*c1*c1 + 8*ep2 + 24*t1*t1)*d**5/120)/cp
    return np.degrees(lam) + lon0, np.degrees(phi)

# ------------------------------------------------------------- web mercator
def merc_x(lon, zoom):  return (np.asarray(lon, float) + 180.0)/360.0 * (2**zoom)
def merc_y(lat, zoom):
    lat = np.radians(np.asarray(lat, float))
    return (1.0 - np.arcsinh(np.tan(lat))/np.pi)/2.0 * (2**zoom)

# ---------------------------------------------------------- polynomial fits
def poly_basis(Xs, Ys, deg):
    cols = [np.ones_like(Xs)]
    for d in range(1, deg+1):
        for i in range(d+1):
            cols.append(Xs**(d-i) * Ys**i)
    return np.stack(cols, -1)
