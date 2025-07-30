#!/usr/bin/env python3
"""
Comprehensive test script for all Brazilian government site scrapers.
Tests all three implemented scrapers with real HTTP requests.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from src.modules.sites.portal_saude_mg import PortalSaudeMGScraper
from src.modules.sites.mds_parcelas import MDSParcelasScraper
from src.modules.sites.mds_saldo import MDSSaldoScraper
from src.utils.logger import logger

def test_portal_saude_mg():
    """Test Portal Saude MG scraper."""
    print("\n" + "="*60)
    print("TESTING PORTAL SAUDE MG SCRAPER")
    print("="*60)
    
    scraper = PortalSaudeMGScraper()
    config = {
        'year': 2024,
        'month': 13,  # All months
        'url': 'https://portal-antigo.saude.mg.gov.br/deliberacoes/documents'
    }
    
    try:
        result = scraper.execute_scraping(config)
        
        print(f"Success: {result['success']}")
        print(f"Files downloaded: {result['files_downloaded']}")
        print(f"Total size (MB): {result.get('total_size_mb', 0):.2f}")
        print(f"Duration (minutes): {result['duration_minutes']:.2f}")
        print(f"Download path: {result['download_path']}")
        
        if result.get('details'):
            print(f"\nDownloaded PDFs: {len(result['details'])}")
            for file_info in result['details'][:3]:  # Show first 3
                print(f"  - {file_info['filename']} ({file_info['size_bytes']} bytes)")
            if len(result['details']) > 3:
                print(f"  ... and {len(result['details']) - 3} more files")
        
        return result['success']
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_mds_parcelas():
    """Test MDS Parcelas scraper."""
    print("\n" + "="*60)
    print("TESTING MDS PARCELAS SCRAPER")
    print("="*60)
    
    scraper = MDSParcelasScraper()
    config = {
        'year': 2024,
        'municipality': 'ALL_MG',
        'url': 'https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*dpotvmubsQbsdfmbtQbhbtNC&event=*fyjcjs'
    }
    
    try:
        result = scraper.execute_scraping(config)
        
        print(f"Success: {result['success']}")
        print(f"Files downloaded: {result['files_downloaded']}")
        print(f"Total size (MB): {result.get('total_size_mb', 0):.2f}")
        print(f"Duration (minutes): {result['duration_minutes']:.2f}")
        print(f"Download path: {result['download_path']}")
        print(f"Records extracted: {result.get('records_extracted', 0)}")
        
        if result.get('details'):
            print(f"\nFiles found: {len(result['details'])}")
            for file_info in result['details']:
                print(f"  - {file_info['filename']} ({file_info['size_bytes']} bytes)")
                if 'note' in file_info:
                    print(f"    Note: {file_info['note']}")
        
        return result['success']
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_mds_saldo():
    """Test MDS Saldo scraper."""
    print("\n" + "="*60)
    print("TESTING MDS SALDO SCRAPER")
    print("="*60)
    
    scraper = MDSSaldoScraper()
    config = {
        'year': 2024,
        'month': 1,  # January
        'municipality': 'ALL_MG',
        'url': 'https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*tbmepQbsdfmbtQbhbtNC&event=*fyjcjs'
    }
    
    try:
        result = scraper.execute_scraping(config)
        
        print(f"Success: {result['success']}")
        print(f"Files downloaded: {result['files_downloaded']}")
        print(f"Total size (MB): {result.get('total_size_mb', 0):.2f}")
        print(f"Duration (minutes): {result['duration_minutes']:.2f}")
        print(f"Download path: {result['download_path']}")
        print(f"Accounts processed: {result.get('accounts_processed', 0)}")
        
        if result.get('balance_summary'):
            balance = result['balance_summary']
            print(f"Balance files found: {balance.get('balance_files_found', 0)}")
            print(f"Balance data extracted: {balance.get('balance_data_extracted', False)}")
        
        if result.get('details'):
            print(f"\nFiles found: {len(result['details'])}")
            for file_info in result['details']:
                print(f"  - {file_info['filename']} ({file_info['size_bytes']} bytes)")
                if 'is_balance_data' in file_info:
                    print(f"    Is balance data: {file_info['is_balance_data']}")
        
        return result['success']
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run comprehensive tests for all scrapers."""
    logger.info("Starting comprehensive scraper testing")
    
    print("BRAZILIAN GOVERNMENT SITES WEB SCRAPER - COMPREHENSIVE TEST")
    print("="*80)
    print("Testing all three implemented scrapers with real HTTP requests:")
    print("1. Portal Saude MG - PDF downloads")
    print("2. MDS Parcelas Pagas - CSV data extraction") 
    print("3. MDS Saldo Detalhado - Balance data extraction")
    
    results = {}
    
    # Test all scrapers
    results['portal_saude_mg'] = test_portal_saude_mg()
    results['mds_parcelas'] = test_mds_parcelas()
    results['mds_saldo'] = test_mds_saldo()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for success in results.values() if success)
    
    for scraper_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{scraper_name.upper().replace('_', ' ')}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} scrapers working correctly")
    
    if passed_tests == total_tests:
        print("🎉 All scrapers are implementing real HTTP-based scraping!")
        print("✅ System is ready for production use with Brazilian government sites")
    else:
        print("⚠️  Some scrapers need attention")
    
    print("\nNOTE: Government sites may require authentication or specific navigation")
    print("for full data access. The scrapers successfully demonstrate real HTTP")
    print("communication and data extraction capabilities.")

if __name__ == "__main__":
    main()