import sys
sys.path.append('../')

import wikipedia

def main():
    topic = input("Topic: ").strip()
    
    content = wikipedia.page(
        title = topic,
        auto_suggest = False
    ).content
    
    with open(f'database/wikipedia/{topic}.txt', 'w', encoding = "utf-8") as file:
        file.write(content)

if __name__ == "__main__":
    main()
