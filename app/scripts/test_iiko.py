"""
Test script to verify iiko API connection and authentication.
Run with: python -m app.scripts.test_iiko
"""
import asyncio
import sys
from app.services.iiko_service import iiko_service
from app.config import settings


async def test_iiko_connection():
    """Test iiko API connection."""
    print("=" * 60)
    print("Testing iiko API Connection")
    print("=" * 60)
    print(f"\nAPI Base URL: {settings.iiko_api_base_url}")
    print(f"Transport Key: {settings.iiko_transport_key[:10]}...")
    print()
    
    try:
        # Test 1: Get access token
        print("Test 1: Getting access token...")
        token = await iiko_service._get_access_token()
        print(f"✓ Successfully obtained access token: {token[:20]}...")
        print()
        
        # Test 2: Get organizations
        print("Test 2: Fetching organizations...")
        organizations = await iiko_service.get_organizations()
        print(f"✓ Successfully fetched {len(organizations)} organizations")
        
        if organizations:
            print("\nOrganizations:")
            for org in organizations[:3]:  # Show first 3
                print(f"  - {org.get('name')} (ID: {org.get('id')})")
            if len(organizations) > 3:
                print(f"  ... and {len(organizations) - 3} more")
        print()
        
        # Test 3: Get nomenclature (if organizations exist)
        if organizations:
            print("Test 3: Fetching nomenclature for first organization...")
            org_id = organizations[0].get('id')
            nomenclature = await iiko_service.get_nomenclature([org_id])
            
            products = nomenclature.get('products', [])
            groups = nomenclature.get('groups', [])
            
            print(f"✓ Successfully fetched nomenclature:")
            print(f"  - Products: {len(products)}")
            print(f"  - Groups: {len(groups)}")
            
            if products:
                print("\nSample products:")
                for product in products[:3]:
                    images_count = len(product.get('images', []))
                    print(f"  - {product.get('name')} (Images: {images_count})")
        print()
        
        # Test 4: Get terminal groups
        if organizations:
            print("Test 4: Fetching terminal groups...")
            org_ids = [org.get('id') for org in organizations[:2]]
            terminal_groups = await iiko_service.get_terminal_groups(org_ids)
            print(f"✓ Successfully fetched {len(terminal_groups)} terminal groups")
            
            if terminal_groups:
                print("\nTerminal groups:")
                for tg in terminal_groups[:2]:
                    items = tg.get('items', [])
                    print(f"  - {tg.get('name')} (Sections: {len(items)})")
        print()
        
        print("=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nPlease check:")
        print("1. Your IIKO_TRANSPORT_KEY is correct")
        print("2. Your internet connection")
        print("3. The iiko API is accessible")
        print("=" * 60)
        return False


if __name__ == "__main__":
    result = asyncio.run(test_iiko_connection())
    sys.exit(0 if result else 1)
