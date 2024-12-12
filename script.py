#import city up here
from dotenv import load_dotenv
import os
from groq import Groq
from chromadb.utils import embedding_functions
from pypdf import PdfReader
from langchain_text_splitters import SentenceTransformersTokenTextSplitter
import chromadb
from termcolor import colored

#load in the environment variable
load_dotenv()
key = os.getenv("API_KEY")

'''RAG stuff'''
def read_doc(file) :
    #read in the document, get the raw text, clean it up as best you can
    reader = PdfReader(f"./docs/{file}.pdf")
    text_list = [p.extract_text().strip() for p in reader.pages]
    text_list = [words for words in text_list if words] #this is a mouthful

    #convert to string
    text = "".join(text_list)

    #splitting the text into smaller chunks
    splitter = SentenceTransformersTokenTextSplitter(
        model_name = "all-MiniLM-L6-v2",
        chunk_size = 500,
        chunk_overlap = 30)
    chunks = splitter.split_text(text)
    return chunks

#gathering chunks from all the documents, could probably do a foreach loop instead of hardcoding...
def gather_chunks():
    chunk_list = []
    chunk_list.append(read_doc("the republic"))
    chunk_list.append(read_doc("crito"))
    chunk_list.append(read_doc("meno"))
    chunk_list.append(read_doc("phaedo"))
    chunk_list.append(read_doc("phaedrus"))
    chunk_list.append(read_doc("symposium"))
    chunk_list.append(read_doc("timaeus"))

    #send the list back out
    return chunk_list

chunk_list = gather_chunks()

''' chroma stuff '''
client = chromadb.Client()
emb_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
chroma_collection = client.create_collection(name = "Plato", embedding_function = emb_func)

def add_chunks():
    #for each list in chunk_list
    for list in enumerate(chunk_list): 
        #for each index and text chunk in chunks:
        for idx, chunk in enumerate(list):
            chroma_collection.add( #add it to the collection
                documents=[chunk],
                metadatas=[{"chunk_index": idx}], #add some metadata to include the index
                ids=[f"doc_{idx}"] #add an ID that also includes the index; doc_0, doc_1, doc_2...
            )

'''messaging'''
#basic LLM setup
chat_client = Groq(api_key = key)

#define some rough... what would the terms be, parameters?
sys_message = {"role": "system", "content": "Your name is Phil. You're a wise philosophy professor whose task is to teach others what you know. Remember to be polite, patient and courteous with users, as you will be teaching people from various walks of life with various backgrounds and beliefs. Don't answer questions that aren't directly related to philosophy, instead politely suggesting that the user ask you about something more on-topic."
}
greeting = {"role": "assistant", "content": "Hello there, my name is Phil. I've spent countless years reading the works of Plato. Would you like to chat?"}
history = [sys_message, greeting]

chat_temp = 0.5
chat_model = "llama-3.1-8b-instant"
chat_tokens = 1000

#print out the greeting
print(colored("Philbot:", "light_green"), greeting.get("content"))

#actual chatting
while True:
    user_msg = input ("(Enter your message): ")
    print()
    print(colored("You:", "blue"), user_msg)
    print()

    #adding in an exit function
    if user_msg == "exit" or user_msg == "bye":
        print(colored("Philbot:", "light_green"), "Have a nice day!")
        break

    history.append({
        "role" : "user",
        "content" : user_msg})
    
    courier = chat_client.chat.completions.create(
        messages = history,
        model = chat_model,
        max_tokens = chat_tokens,
        temperature = chat_temp
    )

    response = courier.choices[0].message.content

    history.append({"role": "assistant", 
                    "content": "response"})

    print(colored("Philbot:", "light_green"), response)

'''
TODO:
-Set up RAG
-Split code into separate functions
-Webpage? Or maybe turn this into a proper application?
-Persona functionality if there's time...
-Could try to get this hosted on Microsoft Azure if I really wanna go above and beyond
'''