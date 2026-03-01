import glob
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from utils.colors import info, warn

INSTALLERS_DIR = "installers"


def _find_neoforge_installer_path(loader_version: str | None) -> str | None:
    """Find NeoForge installer (.jar).

    Supported locations:
    - installers/neoforge-installer.jar (legacy)
    - installers/neoforge/neoforge*-installer*.jar
    - installers/neoforge*-installer*.jar
    """

    legacy_jar = os.path.join(INSTALLERS_DIR, "neoforge-installer.jar")
    if os.path.exists(legacy_jar):
        return legacy_jar

    neoforge_dir = os.path.join(INSTALLERS_DIR, "neoforge")
    patterns = ["neoforge*-installer*.jar", "neoforge-installer*.jar"]

    candidates: list[str] = []
    for pattern in patterns:
        candidates.extend(sorted(glob.glob(os.path.join(neoforge_dir, pattern))))
        candidates.extend(sorted(glob.glob(os.path.join(INSTALLERS_DIR, pattern))))

    if loader_version:
        for path in candidates:
            if loader_version in os.path.basename(path) and os.path.exists(path):
                return path

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def _find_fabric_installer_path() -> str | None:
    """Find Fabric installer (.jar preferred, falls back to .exe).

    Supported locations:
    - installers/fabric-installer.jar (legacy)
    - installers/fabric/fabric-installer*.jar|exe
    - installers/fabric-installer*.jar|exe
    """

    legacy_jar = os.path.join(INSTALLERS_DIR, "fabric-installer.jar")
    if os.path.exists(legacy_jar):
        return legacy_jar

    fabric_dir = os.path.join(INSTALLERS_DIR, "fabric")
    patterns = ["fabric-installer*.jar", "fabric-installer*.exe"]

    candidates: list[str] = []
    for pattern in patterns:
        candidates.extend(sorted(glob.glob(os.path.join(fabric_dir, pattern))))
        candidates.extend(sorted(glob.glob(os.path.join(INSTALLERS_DIR, pattern))))

    for path in candidates:
        if path.lower().endswith(".jar") and os.path.exists(path):
            return path
    for path in candidates:
        if path.lower().endswith(".exe") and os.path.exists(path):
            return path

    return None


def _parse_fabric_installer_version(path: str) -> str | None:
    name = os.path.basename(path)
    m = re.search(r"fabric-installer-(\d+(?:\.\d+)+)\.(?:exe|jar)$", name, re.IGNORECASE)
    return m.group(1) if m else None


def _download_fabric_installer_jar(version: str, dest_path: str) -> bool:
    url = (
        "https://maven.fabricmc.net/net/fabricmc/fabric-installer/"
        f"{version}/fabric-installer-{version}.jar"
    )
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    try:
        info(f"Fabric 인스톨러 JAR 다운로드 중: {version}")
        urllib.request.urlretrieve(url, dest_path)
        return True
    except (urllib.error.URLError, OSError) as e:
        warn(f"Fabric 인스톨러 JAR 다운로드 실패: {e}")
        warn(f"수동 다운로드 URL: {url}")
        return False


def ensure_loader(meta: dict, minecraft_path: str):
    loader = meta.get("loader") if isinstance(meta, dict) else None
    if not loader:
        return

    if loader == "forge":
        install_forge(meta, minecraft_path)
    elif loader == "neoforge":
        install_neoforge(meta, minecraft_path)
    elif loader == "fabric":
        install_fabric(meta, minecraft_path)
    else:
        warn(f"알 수 없는 로더 타입: {loader}")


def install_forge(meta: dict, minecraft_path: str):
    mc_version = meta.get("mc_version")
    loader_version = meta.get("loader_version")

    if not mc_version or not loader_version:
        warn("Forge 설치 메타 정보 부족 (mc_version/loader_version)")
        return

    jar_name = f"forge-{mc_version}-{loader_version}-installer.jar"
    jar_path = os.path.join(INSTALLERS_DIR, jar_name)

    if not os.path.exists(jar_path):
        warn(f"Forge 인스톨러 없음: {jar_name}")
        return

    forge_version_dir = os.path.join(
        minecraft_path,
        "versions",
        f"forge-{mc_version}-{loader_version}",
    )

    if os.path.exists(forge_version_dir):
        info("Forge 이미 설치됨, 설치 단계 생략")
        return

    info("Forge 설치를 위해 인스톨러 GUI가 실행됩니다.")
    info("설치가 완료되면 자동으로 진행됩니다.")
    subprocess.run(
        ["java", "-jar", jar_path],
    )


def install_fabric(meta: dict, minecraft_path: str):
    mc_version = meta.get("mc_version")
    if not mc_version:
        warn("Fabric 설치 메타 정보 부족 (mc_version)")
        return

    installer_path = _find_fabric_installer_path()
    if not installer_path:
        warn(
            "Fabric 인스톨러 없음 (installers/fabric-installer.jar 또는 "
            "installers/fabric/fabric-installer*.jar|exe 를 확인하세요)"
        )
        return

    # If only .exe exists, it may pop up a GUI. Prefer a .jar for headless install.
    if installer_path.lower().endswith(".exe"):
        version = _parse_fabric_installer_version(installer_path) or "1.0.1"
        jar_dest = os.path.join(INSTALLERS_DIR, "fabric", f"fabric-installer-{version}.jar")
        if not os.path.exists(jar_dest):
            if _download_fabric_installer_jar(version, jar_dest):
                installer_path = jar_dest
        else:
            installer_path = jar_dest

    info("Fabric 로더 설치 중...")
    try:
        if installer_path.lower().endswith(".jar"):
            cmd = [
                "java",
                "-jar",
                installer_path,
                "client",
                "-mcversion",
                mc_version,
                "-dir",
                minecraft_path,
            ]
        else:
            cmd = [
                installer_path,
                "client",
                "-mcversion",
                mc_version,
                "-dir",
                minecraft_path,
            ]
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except Exception as e:
        warn(f"Fabric 로더 설치 실패: {e}")


def install_neoforge(meta: dict, minecraft_path: str):
    mc_version = meta.get("mc_version")
    loader_version = meta.get("loader_version")

    if not mc_version or not loader_version:
        warn("NeoForge 설치 메타 정보 부족 (mc_version/loader_version)")
        return

    installer_path = _find_neoforge_installer_path(loader_version)
    if not installer_path:
        warn(
            "NeoForge 인스톨러 없음 (installers/neoforge-installer.jar 또는 "
            "installers/neoforge/neoforge*-installer*.jar 를 확인하세요)"
        )
        return

    version_id = f"neoforge-{mc_version}-{loader_version}"
    version_dir = os.path.join(minecraft_path, "versions", version_id)
    if os.path.exists(version_dir):
        info("NeoForge 이미 설치됨, 설치 단계 생략")
        return

    info("NeoForge 설치를 위해 인스톨러 GUI가 실행됩니다.")
    info("설치가 완료되면 자동으로 진행됩니다.")
    try:
        subprocess.run(
            ["java", "-jar", installer_path],
            check=False,
        )
    except Exception as e:
        warn(f"NeoForge 로더 설치 실패: {e}")


def cleanup_loader(meta: dict, minecraft_path: str):
    loader = meta.get("loader") if isinstance(meta, dict) else None
    if not loader:
        return

    mc_version = meta.get("mc_version")
    loader_version = meta.get("loader_version")

    if loader == "forge":
        if not mc_version or not loader_version:
            warn("Forge 제거 메타 정보 부족 (mc_version/loader_version)")
            return
        _remove_forge(mc_version, loader_version, minecraft_path)
    elif loader == "neoforge":
        if not mc_version or not loader_version:
            warn("NeoForge 제거 메타 정보 부족 (mc_version/loader_version)")
            return
        _remove_neoforge(mc_version, loader_version, minecraft_path)
    elif loader == "fabric":
        if not mc_version:
            warn("Fabric 제거 메타 정보 부족 (mc_version)")
            return
        _remove_fabric(mc_version, minecraft_path)
    else:
        warn(f"알 수 없는 로더 타입: {loader}")


def _remove_forge(mc_version: str, loader_version: str, minecraft_path: str):
    version_id = f"forge-{mc_version}-{loader_version}"
    version_dir = os.path.join(minecraft_path, "versions", version_id)

    if os.path.exists(version_dir):
        info(f"Forge 로더 제거 중: {version_id}")
        try:
            shutil.rmtree(version_dir)
        except Exception as e:
            warn(f"Forge 버전 폴더 제거 실패: {e}")

    lib_dir = os.path.join(minecraft_path, "libraries", "net", "minecraftforge")
    if os.path.exists(lib_dir):
        try:
            shutil.rmtree(lib_dir)
        except Exception as e:
            warn(f"Forge 라이브러리 제거 실패: {e}")


def _remove_fabric(mc_version: str, minecraft_path: str):
    versions_dir = os.path.join(minecraft_path, "versions")
    if not os.path.exists(versions_dir):
        return

    try:
        for name in os.listdir(versions_dir):
            if name.startswith("fabric-loader-") and mc_version in name:
                path = os.path.join(versions_dir, name)
                info(f"Fabric 로더 제거 중: {name}")
                try:
                    shutil.rmtree(path)
                except Exception as e:
                    warn(f"Fabric 버전 폴더 제거 실패: {e}")
    except Exception as e:
        warn(f"Fabric 버전 목록 확인 실패: {e}")

    lib_dir = os.path.join(minecraft_path, "libraries", "net", "fabricmc")
    if os.path.exists(lib_dir):
        try:
            shutil.rmtree(lib_dir)
        except Exception as e:
            warn(f"Fabric 라이브러리 제거 실패: {e}")


def _remove_neoforge(mc_version: str, loader_version: str, minecraft_path: str):
    version_id = f"neoforge-{mc_version}-{loader_version}"
    version_dir = os.path.join(minecraft_path, "versions", version_id)

    if os.path.exists(version_dir):
        info(f"NeoForge 로더 제거 중: {version_id}")
        try:
            shutil.rmtree(version_dir)
        except Exception as e:
            warn(f"NeoForge 버전 폴더 제거 실패: {e}")

    lib_dir = os.path.join(minecraft_path, "libraries", "net", "neoforged")
    if os.path.exists(lib_dir):
        try:
            shutil.rmtree(lib_dir)
        except Exception as e:
            warn(f"NeoForge 라이브러리 제거 실패: {e}")
