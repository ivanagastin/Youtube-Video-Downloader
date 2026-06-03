from gui import YTDownloaderApp

def main():
    try:
        app = YTDownloaderApp()
        app.mainloop()
    except Exception as e:
        print(f"Error starting the application: {e}")

if __name__ == "__main__":
    main()
