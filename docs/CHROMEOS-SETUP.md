# ChromeOS Setup (Crostini)

1. Settings -> Advanced -> Developers -> Linux development environment -> Turn on.
2. Files app -> right-click USB drive -> Share with Linux -> /mnt/chromeos/removable/<DRIVE>/.
3. Linux Terminal:
   cd /mnt/chromeos/removable/<DRIVE>/aegis-drive
   python3 download_models.py --core ornith-9b-cortex   # one-time, hash-verified
   ./serve-model.sh ornith-9b-cortex                    # llama.cpp is bundled
   # or: python3 serve.py -> http://127.0.0.1:8080 for the wllama drive UI
4. Optional Docker: docker compose -f stack/docker-compose.yml up -d (:8080, :8443).
5. Truth table: 9B CORTEX cores = daily drivers here. muse-glimmer-30b = no (8 GB physics).
