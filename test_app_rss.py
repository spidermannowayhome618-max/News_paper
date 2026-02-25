import sys
sys.path.append('c:/harsh/News_paper')

from app import get_news_data

print("Testing RSS feed fetching...")
try:
    news_data = get_news_data()
    
    print(f"\n=== RSS FEED RESULTS ===")
    for category, articles in news_data.items():
        print(f"{category}: {len(articles)} articles")
        if articles:
            print(f"  First article: {articles[0]['title'][:50]}...")
        else:
            print("  No articles found")
    
    # Check specifically for Politics and Lifestyle
    print(f"\n=== PROBLEMATIC CATEGORIES ===")
    politics_key = None
    lifestyle_key = None
    
    for key in news_data.keys():
        if 'Politics' in key or '🏛️' in key:
            politics_key = key
        if 'Lifestyle' in key or '🏥' in key:
            lifestyle_key = key
    
    if politics_key:
        print(f"Politics ({politics_key}): {len(news_data[politics_key])} articles")
    else:
        print("Politics category not found!")
        
    if lifestyle_key:
        print(f"Lifestyle & Health ({lifestyle_key}): {len(news_data[lifestyle_key])} articles")
    else:
        print("Lifestyle & Health category not found!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
