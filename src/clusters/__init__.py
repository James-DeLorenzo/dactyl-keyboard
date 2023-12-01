from clusters.carbonfet import CarbonfetCluster
from clusters.custom_cluster import CustomCluster
from clusters.default_cluster import DefaultCluster
from clusters.mini import MiniCluster
from clusters.minidox import MinidoxCluster
from clusters.minithicc import Minithicc
from clusters.minithicc3 import Minithicc3
from clusters.trackball_btu import TrackballBTU
from clusters.trackball_cj import TrackballCJ
from clusters.trackball_orbyl import TrackballOrbyl
from clusters.trackball_three import TrackballThree
from clusters.trackball_wilder import TrackballWild


def Cluster(settings, helper, wallbuilder, other_thumb=False, **kwargs):
        style = settings["thumb_style"] if not other_thumb else settings["other_thumb"]
        if style == CarbonfetCluster.name:
            return CarbonfetCluster(settings, helper, wallbuilder, **kwargs)
        elif style == MiniCluster.name:
            return MiniCluster(settings, helper, **kwargs)
        elif style == MinidoxCluster.name:
            return MinidoxCluster(settings, helper, **kwargs)
        elif style == Minithicc.name:
            return Minithicc(settings, helper, **kwargs)
        elif style == Minithicc3.name:
            return Minithicc3(settings, helper, **kwargs)
        elif style == TrackballOrbyl.name:
            return TrackballOrbyl(settings, helper, **kwargs)
        elif style == TrackballWild.name:
            return TrackballWild(settings, helper, **kwargs)
        elif style == TrackballThree.name:
            return TrackballThree(settings, helper, **kwargs)
        elif style == TrackballBTU.name:
            return TrackballBTU(settings, helper, **kwargs)
        elif style == TrackballCJ.name:
            return TrackballCJ(settings, helper, **kwargs)
        elif style == CustomCluster.name:
            return CustomCluster(settings, helper, **kwargs)
        else:
            return DefaultCluster(settings, helper, wallbuilder, **kwargs)

