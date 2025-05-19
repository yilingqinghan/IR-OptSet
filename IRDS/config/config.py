import os
import yaml

class ToolchainConfig:
    def __init__(self):
        self._load_settings()
        self._validate()

    def _load_settings(self):
        config_path = os.path.join(os.path.dirname(__file__), "settings.yaml")
        settings = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                settings = yaml.safe_load(f) or {}

        self.clang = settings.get("clang") or os.environ.get("CLANG_PATH")
        self.clangpp = settings.get("clangpp") or os.environ.get("CLANGPP_PATH")
        self.opt = settings.get("opt") or os.environ.get("OPT_PATH")
        self.flang = settings.get("flang") or os.environ.get("FLANG_PATH")
        self.extralib = settings.get("extralib") or os.environ.get("EXTRA_LIB_PATH")
        self.wandb = settings.get("wandb") or os.environ.get("WANB_API")
        self.llvm = settings.get("llvm") or os.environ.get("LLVM_SRC")
        self.llvm_nm = settings.get("llvm_nm") or os.environ.get("NM_PATH")
        self.llvm_extract = settings.get("llvm_extract") or os.environ.get("EX_PATH")
        self.llvm_dis = settings.get("llvm_dis") or os.environ.get("DIS_PATH")
        self.llvm_as = settings.get("llvm_as") or os.environ.get("AS_PATH")
        self.llvm_mca = settings.get("llvm_mca") or os.environ.get("MCA_PATH")
        self.llc = settings.get("llc") or os.environ.get("LLC_PATH")
        self.tokenizer = settings.get("tokenizer") or os.environ.get("TOKENIZER_MODEL")
        self.alive2 = settings.get("alive2") or os.environ.get("ALIVE2")

    def _validate(self):
        missing = []
        for attr in ["clang", "opt", "clangpp", "flang"]:
            if getattr(self, attr) is None:
                missing.append(attr.upper() + "_PATH")
        if missing:
            raise EnvironmentError(f"🌈Please set environment variables: {', '.join(missing)}")

    def __repr__(self):
        return (
            f"ToolchainConfig(clang={self.clang}, opt={self.opt}, clangpp={self.clangpp}, flang={self.flang}, extralib = {self.extralib}, wandb = {self.wandb}), llvm={self.llvm}"
        )