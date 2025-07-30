"""
Brazilian Government Sites Scrapers

This package contains specialized scrapers for Brazilian government sites:
- Portal Saude MG: Health department resolutions (PDFs)
- MDS Parcelas: Social development payment data
- MDS Saldo: Detailed account balance data
"""

from .portal_saude_mg import PortalSaudeMGScraper
from .mds_parcelas import MDSParcelasScraper  
from .mds_saldo import MDSSaldoScraper

__all__ = [
    'PortalSaudeMGScraper',
    'MDSParcelasScraper', 
    'MDSSaldoScraper'
]