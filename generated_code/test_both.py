import streamlit as st

def main():
    st.title("Kazuri Test App")
    st.write("This is a test of both terminal and browser functionality")
    
    # Terminal output
    print("This will show in the terminal")
    
    # Browser output
    st.write("This will show in the browser")
    if st.button("Click me"):
        st.success("Button clicked!")

if __name__ == "__main__":
    print("Starting Streamlit app...")
    main()
