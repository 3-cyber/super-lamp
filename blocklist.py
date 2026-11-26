import os
import re
import urllib.parse
from pathlib import Path
from typing import Set, List, Optional
import requests
from config import BLOCKLIST_FILE, CUSTOM_BLOCKLIST_FILE

CORE_ADULT_DOMAINS = [
    # Top Tube Sites
    "pornhub.com", "xvideos.com", "xnxx.com", "xhamster.com", "youporn.com",
    "redtube.com", "tube8.com", "spankbang.com", "eporner.com", "beeg.com",
    "txxx.com", "hqporner.com", "thumbzilla.com", "daftsex.com", "upornia.com",
    "porntrex.com", "pornktube.com", "severeporn.com", "vxxx.com", "fuq.com",
    "pornhat.com", "anyporn.com", "4tube.com", "porndoe.com", "alohatube.com",
    "hdporn92.com", "fapvid.com", "freeomovie.com", "tubegalore.com", "nudevista.com",
    "ixxx.com", "porn300.com", "palimas.com", "pornve.com", "slutload.com",
    "drtuber.com", "tnaflix.com", "empflix.com", "hotmovs.com", "cliphunter.com",
    "bravoteens.com", "flyflv.com", "xfreehd.com", "pornmd.com", "pornrabbit.com",
    "fuskator.com", "pornone.com", "sunporno.com", "porntube.com", "sublimeporn.com",

    # Cams & Interactive
    "chaturbate.com", "stripchat.com", "camsoda.com", "bongacams.com", "myfreecams.com",
    "livejasmin.com", "cam4.com", "flirt4free.com", "imlive.com", "streamate.com",
    "camversity.com", "camcontacts.com", "naked.com", "fleshlight.com",

    # Paid / Premium Studio Sites & Networks
    "brazzers.com", "bangbros.com", "naughtyamerica.com", "realitykings.com", "mofos.com",
    "evilangel.com", "digitalplayground.com", "twistys.com", "babes.com", "sweetinner.com",
    "kink.com", "blacked.com", "tushy.com", "vixen.com", "deeper.com", "slayxx.com",
    "wicked.com", "hustler.com", "penthouse.com", "playboy.com", "rk.com", "puremature.com",
    "teamskeet.com", "passion-hd.com", "sislovesme.com", "familystrokes.com", "bratsis.com",
    "stepsiblingscaught.com", "momxxx.com", "pervmom.com", "mylf.com", "nubiles.net",
    "eroticax.com", "lustery.com", "bellesa.co", "x-art.com", "femjoy.com", "met-art.com",
    "ftvgirls.com", "hegre.com", "watchdata.com", "alsangels.com", "joymii.com",

    # OnlyFans / Fansites / Leaks
    "onlyfans.com", "fansly.com", "fapello.com", "coomer.party", "coomer.su",
    "kemono.party", "kemono.su", "simpcity.su", "thothub.to", "dirtyship.com",
    "leakedzone.com", "xbunker.is", "erome.com", "bunkr.is", "bunkrr.su", "gofile.io",

    # Hentai / Anime / 3D Adult Sites & Doujinshi
    "nhentai.net", "hanime.tv", "hentaihaven.xxx", "hentaihaven.me", "tsumino.com", "pururin.io",
    "hitomi.la", "e-hentai.org", "exhentai.org", "luscious.net", "rule34.xxx",
    "rule34video.com", "rule34.paheal.net", "gelbooru.com", "danbooru.donmai.us", "hypnohub.net",
    "hentai2read.com", "simply-hentai.com", "multporn.net", "8muses.com", "hentaidude.com",
    "hentaistream.xxx", "hentaimama.io", "asmhentai.com", "hentaifox.com", "hentaiera.com",
    "hentai-foundry.com", "fakku.net", "doujins.com", "muchohentai.com", "uncensoredhentai.xxx",
    "hentaicity.com", "hentaiworld.tv", "3dhentaitube.com", "hentai-moon.com", "hentairox.com",
    "hentaivn.net", "javhentai.xxx", "hentai007.com", "hentaibar.com", "underhentai.net",
    "sankakucomplex.com", "chan.sankakucomplex.com", "yande.re", "e-shuushuu.net", "tbib.org",
    "hentaimanga.me", "submanga.io", "cartoonpornvideos.com", "animeporn.tv", "hentaicloud.com",

    # NSFW AI & Adult Generator Sites
    "civitai.red", "civitai.com", "pornpen.ai", "seduced.ai", "unprompt.ai", "sexy.ai",

    # VR Porn
    "wankzvr.com", "sexlikereal.com", "vrsmash.com", "badoinkvr.com", "virtualrealporn.com",
    "czechvr.com", "stripchatvr.com", "vrph.com", "vrbangers.com",

    # Escort / Hookup / Adult Dating
    "adultfriendfinder.com", "ashleymadison.com", "fetlife.com", "alt.com",
    "bedpage.com", "listcrawler.com", "skipthegames.com", "eros.com",

    # Adult Forum & Directories
    "theporndude.com", "porndude-cams.com", "planetsuzy.org", "vipergirls.to",
    "vintage-erotica-forum.com", "thotslife.com", "famousboard.com",

    # Gay Adult Tube Sites
    "boyfantasy.com", "gaypornhd.com", "machotube.tv", "gaymaletube.com", "porngay.xxx",
    "manporno.com", "cockhero.info", "tubeguys.com", "homo.xxx", "gayporn.fm",
    "mygaytube.tv", "timtales.com", "sexxx.xxx", "nakedsword.com", "gaybeeg.info",
    "gayporno.tv", "freegayporn.tv", "maleporn.com", "boyporn.tv", "gayboystube.com",
    "hunkystuff.com", "menonfilms.com", "twinkboys.com", "twinktop.com", "gayxtube.com",
    "gayforfans.com", "gaywire.com", "gayfuror.com", "queerclick.com", "fapgay.com",
    "xtube.com", "nextdoorhookups.com", "boysfood.com", "hotmen.com", "gayfuckporn.com",

    # Gay Adult Studios & Networks
    "men.com", "corbinfisher.com", "nextdoorbuddies.com", "lucasentertainment.com",
    "helixstudios.com", "sean-cody.com", "seancody.com", "belamionline.com", "ragingstallion.com",
    "cockyboys.com", "falconstudios.com", "brokestraightboys.com", "peterfever.com",
    "fratmen.tv", "sayuncle.com", "rawfuckboys.com", "badpuppy.com", "staxus.com",
    "coltstudio.com", "menatplay.com", "chubbyboys.com", "bearfilms.com", "activeduty.com",
    "latinoguysporn.com", "chaosmen.com", "nextdoorstudios.com", "c1r.com", "breeddicks.com",
    "scaredstiff.com", "maskurban.com", "treasureislandmedia.com", "barebackrt.com",
    "hunkvideo.com", "titanmen.com", "channel1releasing.com", "dr9.com",

    # Gay Cams & Interactive
    "cam4boys.com", "gaycamvideos.net", "flirt4free.com", "camsoda.com",
    "menlovers.com", "boycam.xxx", "malecams.com", "gaycams.com",

    # Gay Dating / Cruising / Hookup / Escort Sites
    "grindr.com", "scruff.com", "sniffies.com", "squirt.org", "rentmen.com",
    "rentmen.eu", "rentmasseur.com", "planetromeo.com", "gayromeo.com", "manhunt.net",
    "recon.com", "adam4adam.com", "gaydar.net", "silverdaddies.com", "barebackbastards.com",

    # Gay Hentai / Yaoi / Bara
    "myreadingmanga.info", "yaoi-haven.com", "bara-manga.com", "yaoicomics.com",
    "fujoshi.info", "yaoigasm.com", "doujinshi.org",

    # Gay Directories & Forums
    "thegaydude.com", "thegaydude.net", "gay-torrents.net", "gaytorrents.org",
    "queermenow.net", "str8upgayporn.com", "smutjunkies.com", "waybig.com",
    "boypornlist.com", "menofporn.com",

    # Transgender / Shemale / Femboy Adult Sites
    "shemale.xxx", "transporn.com", "ts-dating.com", "transangels.com", "shemalestube.com",
    "grooby.com", "femboyporn.com", "shemaleclub.com", "trannyvideos.xxx"
]

ADULT_KEYWORDS = [
    r"\bporn\b", r"\bxxx\b", r"\bhentai\b", r"\bxvideos\b", r"\bpornhub\b",
    r"\bxhamster\b", r"\bblowjob\b", r"\bhardcore\b", r"\berotic\b",
    r"\bnude\b", r"\bnaked\b", r"\bcamgirl\b", r"\bstripchat\b", r"\bchaturbate\b",
    r"\bnsfw\b", r"\bonlyfans\b", r"\bbabes\b", r"\bmilf\b", r"\bbusty\b",
    r"\bcumshot\b", r"\bcreampie\b", r"\bgangbang\b", r"\borgasm\b",
    r"\bdildo\b", r"\bmasturbat", r"\bdeepthroat\b", r"\banal sex\b", r"\bsex video\b",

    # Gay & Trans Adult Keywords
    r"\bgay porn\b", r"\bgay xxx\b", r"\bgay sex\b", r"\bgay tube\b", r"\bmale tube\b",
    r"\bgaymaletube\b", r"\bcorbin fisher\b", r"\bseancody\b", r"\bsean cody\b",
    r"\bmen\.com\b", r"\bhelix studios\b", r"\bhelixstudios\b", r"\braging stallion\b",
    r"\bfalcon studios\b", r"\bcockyboys\b", r"\bboyfantasy\b", r"\bmachotube\b",
    r"\bbareback\b", r"\btwink\b", r"\byaoi\b", r"\bbara\b",
    r"\bfemboy porn\b", r"\bshemale\b", r"\btrans porn\b", r"\bladyboy\b", r"\btranny\b",
    r"\bgay cam\b", r"\bgay webcam\b", r"\bgay escort", r"\bgloryhole\b", r"\bgay cruising\b",
    r"\brentmen\b", r"\bsniffies\b", r"\bthegaydude\b", r"\bwaybig\b", r"\bqueermenow\b",

    # Hentai / Doujinshi / Anime / AI Adult Keywords
    r"\bhentai\b", r"\bdoujin\b", r"\bdoujinshi\b", r"\becchi\b", r"\bahegao\b",
    r"\bhanime\b", r"\bnhentai\b", r"\brule34\b", r"\bgelbooru\b", r"\bfakku\b",
    r"\bhentaidude\b", r"\basmhentai\b", r"\bhentaifox\b", r"\bhentaimama\b",
    r"\bcivitai\b"
]

ONLINE_BLOCKLIST_SOURCES = [
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/porn/hosts",
    "https://nsfw.oisd.nl/domainswg"
]

class BlocklistManager:
    def __init__(self, blocklist_file=BLOCKLIST_FILE, custom_file=CUSTOM_BLOCKLIST_FILE):
        self.blocklist_file = Path(blocklist_file)
        self.custom_file = Path(custom_file)
        self.domains: Set[str] = set()
        self.keyword_patterns: List[re.Pattern] = []
        self.load_blocklist()

    def _clean_domain(self, domain_str: str) -> Optional[str]:
        domain_str = domain_str.strip().lower()
        if not domain_str or domain_str.startswith("#"):
            return None
        parts = domain_str.split()
        if len(parts) >= 2 and (parts[0] in ("0.0.0.0", "127.0.0.1", "::1")):
            domain_str = parts[1]
        elif len(parts) >= 1:
            domain_str = parts[0]
        
        if "://" in domain_str:
            try:
                parsed = urllib.parse.urlparse(domain_str)
                domain_str = parsed.netloc or parsed.path
            except Exception:
                pass
        
        domain_str = domain_str.split("/")[0].split(":")[0].strip()
        domain_str = domain_str.lstrip(".")
        if domain_str.startswith("www."):
            domain_str = domain_str[4:]
        
        if len(domain_str) > 3 and "." in domain_str:
            return domain_str
        return None

    def _rebuild_keyword_patterns(self):
        all_kw = list(ADULT_KEYWORDS)
        # Add root words from core domains
        for dom in CORE_ADULT_DOMAINS:
            root = dom.split(".")[0].strip().lower()
            if len(root) >= 4 and not root.isdigit():
                pattern = rf"\b{re.escape(root)}\b"
                if pattern not in all_kw:
                    all_kw.append(pattern)

        # Also add root words and full domain patterns from custom domains
        if self.custom_file.exists():
            try:
                with open(self.custom_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        cdom = self._clean_domain(line)
                        if cdom:
                            dom_pat = rf"{re.escape(cdom)}"
                            if dom_pat not in all_kw:
                                all_kw.append(dom_pat)
                            croot = cdom.split(".")[0].strip().lower()
                            if len(croot) >= 3 and not croot.isdigit():
                                root_pat = rf"\b{re.escape(croot)}\b"
                                if root_pat not in all_kw:
                                    all_kw.append(root_pat)
            except Exception:
                pass

        self.keyword_patterns = [
            re.compile(kw, re.IGNORECASE) for kw in all_kw
        ]

    def load_blocklist(self):
        self.domains.clear()
        for d in CORE_ADULT_DOMAINS:
            cleaned = self._clean_domain(d)
            if cleaned:
                self.domains.add(cleaned)

        if self.blocklist_file.exists():
            try:
                with open(self.blocklist_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        cleaned = self._clean_domain(line)
                        if cleaned:
                            self.domains.add(cleaned)
            except Exception as e:
                pass

        if self.custom_file.exists():
            try:
                with open(self.custom_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        cleaned = self._clean_domain(line)
                        if cleaned:
                            self.domains.add(cleaned)
            except Exception as e:
                pass

        self._rebuild_keyword_patterns()

        if not self.blocklist_file.exists() and self.domains:
            self.save_blocklist()

    def save_blocklist(self):
        try:
            self.blocklist_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.blocklist_file, "w", encoding="utf-8") as f:
                f.write("# Adult Domains Blocklist\n")
                for d in sorted(self.domains):
                    f.write(f"{d}\n")
        except Exception as e:
            pass

    def add_custom_domain(self, domain: str) -> bool:
        cleaned = self._clean_domain(domain)
        if not cleaned:
            return False
        self.domains.add(cleaned)
        try:
            self.custom_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.custom_file, "a", encoding="utf-8") as f:
                f.write(f"{cleaned}\n")
            self._rebuild_keyword_patterns()
            return True
        except Exception:
            return False

    def is_domain_blocked(self, candidate_domain: str) -> bool:
        cleaned = self._clean_domain(candidate_domain)
        if not cleaned:
            return False

        if cleaned in self.domains:
            return True

        parts = cleaned.split(".")
        for i in range(1, len(parts) - 1):
            parent_domain = ".".join(parts[i:])
            if parent_domain in self.domains:
                return True
        return False

    def is_text_suspicious(self, text: str) -> bool:
        if not text:
            return False
        for pattern in self.keyword_patterns:
            if pattern.search(text):
                return True
        return False

    def sync_online_blocklist(self, max_domains: int = 75000) -> int:
        initial_count = len(self.domains)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        for url in ONLINE_BLOCKLIST_SOURCES:
            try:
                resp = requests.get(url, headers=headers, timeout=20)
                if resp.status_code == 200:
                    lines = resp.text.splitlines()
                    for line in lines:
                        cleaned = self._clean_domain(line)
                        if cleaned:
                            self.domains.add(cleaned)
                            if len(self.domains) >= max_domains:
                                break
                    if len(self.domains) >= max_domains:
                        break
            except Exception:
                pass

        self.save_blocklist()
        return len(self.domains) - initial_count
