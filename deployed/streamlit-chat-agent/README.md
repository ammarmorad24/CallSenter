# Streamlit Chat Agent

This project is a chat agent application built using Python, Streamlit, and WebSockets. It allows users to interact with a chat agent through a web interface.

## Project Structure

```
streamlit-chat-agent
├── src
│   ├── main.py          # Chat agent application logic
│   └── streamlit_app.py # Streamlit application entry point
├── requirements.txt     # Project dependencies
└── README.md            # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
      git clone <repository-url>
         cd streamlit-chat-agent
            ```

            2. **Create a virtual environment (optional but recommended):**
               ```
                  python -m venv venv
                     source venv/bin/activate  # On Windows use `venv\Scripts\activate`
                        ```

                        3. **Install the required dependencies:**
                           ```
                              pip install -r requirements.txt
                                 ```

                                 ## Usage

                                 1. **Run the Streamlit application:**
                                    ```
                                       streamlit run src/streamlit_app.py
                                          ```

                                          2. **Open your web browser and navigate to:**
                                             ```
                                                http://localhost:8501
                                                   ```

                                                   3. **Interact with the chat agent through the web interface.**

                                                   ## Dependencies

                                                   - Streamlit
                                                   - websockets
                                                   - asyncio
                                                   - json
                                                   - random

                                                   ## License

                                                   This project is licensed under the MIT License. See the LICENSE file for details.