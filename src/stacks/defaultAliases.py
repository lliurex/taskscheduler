import gettext
_ = gettext.gettext

i18n={"LLX_UP":_("LliureX upgrade (with mirror)"),
	"LLX_US":_("LliureX upgrade (only system)"),
	"MRR_UP":_("Mirror upgrade"),
	"APT_CL":_("Clean apt cache")
	}


aliases={i18n["LLX_UP"]:"/usr/sbin/lliurex-upgrade -u",
	i18n["LLX_US"]:"/usr/sbin/lliurex-upgrade -u -r",
	i18n["MRR_UP"]:"/usr/sbin/lliurex-mirror -u",
	i18n["APT_CL"]:"/usr/bin/apt clean"
	}

def getDefaults():
	return(aliases)	
