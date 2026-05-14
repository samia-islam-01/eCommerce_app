import tweepy
from django.conf import settings


def get_x_client():
    client = tweepy.Client(
        consumer_key=settings.X_API_KEY,
        consumer_secret=settings.X_API_SECRET,
        access_token=settings.X_ACCESS_TOKEN,
        access_token_secret=settings.X_ACCESS_SECRET,
    )

    return client


def tweet_new_store(store):
    client = get_x_client()

    message = (
        f"New Store Added!\n\n"
        f"{store.name}\n"
        f"{store.description}"
    )

    try:
        response = client.create_tweet(text=message)

        print("STORE TWEET SENT")
        print(response)

    except Exception as e:
        print("STORE TWEET FAILED")
        print(type(e))
        print(e)


def tweet_new_product(product):
    client = get_x_client()

    message = (
        f"New Product Added!\n\n"
        f"Store: {product.store.name}\n"
        f"Product: {product.name}\n"
        f"{product.description}"
    )

    try:
        response = client.create_tweet(text=message)

        print("PRODUCT TWEET SENT")
        print(response)

    except Exception as e:
        print("PRODUCT TWEET FAILED")
        print(type(e))
        print(e)