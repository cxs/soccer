import re

def read_and_parse_text(filename):
    with open(filename, 'r') as file:
        text = file.read()

    features = re.split(r'\d\.\)', text)[1:]  # Skip the first empty element
    features = [feature.strip() for feature in features]

    return features

def main():
    filename = "features.txt"
    features = read_and_parse_text(filename)
    #read file app.py into memory
    with open('app.py', 'r') as file:
        code = file.read()
    print("Features:")
    for i, feature in enumerate(features):
        print(f"{i + 1}. {feature[:80]}...")

    selected_feature = int(input("Pick a feature number (1-6): ")) - 1
    print(f"\nFeature {selected_feature + 1}:\n{features[selected_feature]}\n")
    print(f"\n------------------------------------------------------------ \n")
    print(f"""I want you to read the following code and rewrite it to include the feature mentioned below.
      Just add the feature to the code, don't remove anything. Respond with formatted  parts of the code which have changed.\n""")
    print(f"\nCode:\n{code}\n")
    print(f"\nNew feature: ADD {features[selected_feature]}\n")
    print (f"\n------------------------------------------------------------ \n")

        

if __name__ == '__main__':
    main()
