"""
Brazilian Government Sites Scrapers

This package contains specialized scrapers for Brazilian government sites:
- Portal Saude MG: Health department resolutions (PDF)
- MDS Parcelas: Social development payment data (CSV)
- MDS Saldo: Detailed account balance data (CSV)
"""

from .portal_saude_mg import PortalSaudeMGScraper
# from .mds_parcelas import MDSParcelasScraper  # Commented out - class not implemented yet
# from .mds_saldo import MDSSaldoScraper  # Commented out - class not implemented yet

__all__ = [
    'PortalSaudeMGScraper',
    #'MDSParcelasScraper', 
    #'MDSSaldoScraper'
]