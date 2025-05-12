def read_config(file_path="settings.config") -> dict:
    config_values = {}
    with open(file_path, "r") as f:
        for line in f:
            # Skip comments and empty lines
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                config_values[key.strip()] = value.strip()
    return config_values


def update_config(key: str, value: str, file_path="settings.config") -> dict:
    lines = []
    key_found = False

    with open(file_path, "r") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("#") or not stripped or "=" not in stripped:
                lines.append(line)
                continue

            current_key, _ = stripped.split("=", 1)
            if current_key.strip() == key:
                lines.append(f"{key}={value}\n")
                key_found = True
            else:
                lines.append(line)

    if not key_found:
        raise KeyError(f"{key} not found in {file_path}")

    with open(file_path, "w") as f:
        f.writelines(lines)

    return read_config(file_path)

