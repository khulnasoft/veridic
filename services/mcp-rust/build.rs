fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .compile(
            &["proto/mcp.proto", "proto/ai_service.proto"],
            &["proto"],
        )?;
    Ok(())
}
