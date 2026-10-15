import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
anon_key = os.getenv("SUPABASE_ANON_KEY")

def login(email, password):
    client = create_client(url, anon_key)
    client.auth.sign_in_with_password({"email": email, "password": password})
    return client

# Log in as Alice, insert a document as Alice
alice = login("alice@test.com", "alice123")
alice.table("documents").insert({
    "user_id": alice.auth.get_user().user.id,
    "filename": "alice_doc.pdf"
}).execute()

# Log in as Bob, try to see Alice's documents
bob = login("bob@test.com", "bob123")
bob_view = bob.table("documents").select("*").execute()
print("Bob sees:", bob_view.data)

alice_view = alice.table("documents").select("*").execute()
print("Alice sees:", alice_view.data)

session = alice.auth.get_session()
print(session.access_token)