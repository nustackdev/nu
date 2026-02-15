# Engineering — Project Structure

```text
everylens/
├── docs/
│   ├── vision.md
│   ├── model.md
│   ├── design/
│   └── engineering/
├── web/                    # React frontend
│   ├── src/
│   │   ├── components/     # Shape/Slot/Primitive renderers
│   │   ├── stores/         # schema store, data store
│   │   ├── ws/             # WebSocket client, Term serialization
│   │   └── App.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── api/                    # Python backend
│   ├── src/everylens/
│   │   ├── server.py       # WebSocket handler
│   │   ├── schema.py       # Shape introspection → JSON
│   │   └── evaluate.py     # Term deserialization + evaluation
│   └── pyproject.toml
├── Makefile
└── README.md
```

Frontend and backend are independent packages in one repo. No shared code — they communicate only through the WebSocket protocol.

`web/` is a standalone Vite + React app. `api/` is a standalone Python package with everybase as a dependency. Either can be developed, tested, and built independently.
