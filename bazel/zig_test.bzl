"""Compile and run a bounded Zig test module with a child-pinned toolchain."""

def _crypto_ecosystems_zig_test_binary_impl(ctx):
    source = ctx.file.source
    archive = ctx.file.archive
    test_binary = ctx.outputs.executable

    ctx.actions.run(
        executable = ctx.executable.compiler,
        tools = [ctx.attr.compiler[DefaultInfo].files_to_run],
        inputs = [archive, source],
        outputs = [test_binary],
        arguments = [archive.path, source.path, test_binary.path],
        mnemonic = "ZigTestCompile",
        progress_message = "Compiling Zig tests with pinned toolchain for %s" % ctx.label,
    )

    return [DefaultInfo(files = depset([test_binary]), executable = test_binary)]

def _crypto_ecosystems_zig_test_impl(ctx):
    test_binary = ctx.outputs.executable
    ctx.actions.symlink(
        output = test_binary,
        target_file = ctx.executable.binary,
        is_executable = True,
    )
    return [DefaultInfo(
        executable = test_binary,
        runfiles = ctx.attr.binary[DefaultInfo].default_runfiles,
    )]

crypto_ecosystems_zig_test_binary = rule(
    implementation = _crypto_ecosystems_zig_test_binary_impl,
    executable = True,
    attrs = {
        "archive": attr.label(mandatory = True, allow_single_file = [".tar.xz"]),
        "compiler": attr.label(mandatory = True, executable = True, cfg = "exec"),
        "source": attr.label(mandatory = True, allow_single_file = [".zig"]),
    },
)

crypto_ecosystems_zig_test = rule(
    implementation = _crypto_ecosystems_zig_test_impl,
    test = True,
    attrs = {
        "binary": attr.label(mandatory = True, executable = True, cfg = "target"),
    },
)
