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

        self.clang = os.environ.get("CLANG_PATH") or settings.get("clang")
        self.clangpp = os.environ.get("CLANGPP_PATH") or settings.get("clangpp")
        self.opt = os.environ.get("OPT_PATH") or settings.get("opt")
        self.flang = os.environ.get("FLANG_PATH") or settings.get("flang")
        self.extralib = os.environ.get("EXTRA_LIB_PATH") or settings.get("extralib")
        self.wandb = os.environ.get("WANB_API") or settings.get("wandb")
        self.llvm = os.environ.get("LLVM_SRC") or settings.get("llvm")
        self.llvm_nm = os.environ.get("NM_PATH") or settings.get("llvm_nm")
        self.llvm_extract = os.environ.get("EX_PATH") or settings.get("llvm_extract")
        self.llvm_dis = os.environ.get("DIS_PATH") or settings.get("llvm_dis")
        self.llvm_as = os.environ.get("AS_PATH") or settings.get("llvm_as")
        self.llvm_mca = os.environ.get("MCA_PATH") or settings.get("llvm_mca")
        self.llc = os.environ.get("LLC_PATH") or settings.get("llc")
        self.tokenizer = os.environ.get("TOKENIZER_MODEL") or settings.get("tokenizer")
        self.alive2 = os.environ.get("ALIVE2") or settings.get("alive2")

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