from messageAPI import FloodProxy

def main():
    print("Creating Flood Proxy.")
    fb = FloodProxy()
    print("Running Flood Proxy.")
    fb.run()
    print("This comes after a true loop and should not be visible.")
    print("Error in the Flood Proxy app.")

if __name__ == '__main__':
    main()
