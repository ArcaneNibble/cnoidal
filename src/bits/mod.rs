pub mod lxt;
pub mod lxt2;
pub mod vzt;

// LXT/LXT2/VZT
pub const LXT_FLAG_INTEGER: u32 = 1 << 1;
pub const LXT_FLAG_DOUBLE: u32 = 1 << 1;
pub const LXT_FLAG_STRING: u32 = 1 << 2;
pub const LXT_FLAG_ALIAS: u32 = 1 << 3;

// LXT2/VZT
pub const LXT2_FLAG_SIGNED: u32 = 1 << 4;
pub const LXT2_FLAG_BOOLEAN: u32 = 1 << 5;
pub const LXT2_FLAG_NATURAL: u32 = (1 << 6) | (LXT_FLAG_INTEGER);
pub const LXT2_FLAG_POSITIVE: u32 = (1 << 7) | (LXT_FLAG_INTEGER);
pub const LXT2_FLAG_CHARACTER: u32 = 1 << 8;
pub const LXT2_FLAG_CONSTANT: u32 = 1 << 9;
pub const LXT2_FLAG_VARIABLE: u32 = 1 << 10;
pub const LXT2_FLAG_SIGNAL: u32 = 1 << 11;

pub const LXT2_FLAG_IN: u32 = 1 << 12;
pub const LXT2_FLAG_OUT: u32 = 1 << 13;
pub const LXT2_FLAG_INOUT: u32 = 1 << 14;

pub const LXT2_FLAG_WIRE: u32 = 1 << 15;
pub const LXT2_FLAG_REG: u32 = 1 << 16;
