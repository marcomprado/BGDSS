"""
Brazilian Government Sites Scrapers

This package contains specialized scrapers for Brazilian government sites:
- Portal Saude MG: Health department resolutions (PDF)
- MDS Parcelas: Social development payment data (CSV)
- MDS Saldo: Detailed account balance data (CSV)
"""

from .portal_saude_mg import PortalSaudeMGScraper
from .mds_parcelas import MDSParcelasScraper
from .mds_saldo import MDSSaldoScraper

__all__ = [
    'PortalSaudeMGScraper',
    'MDSParcelasScraper', 
    'MDSSaldoScraper'
]