(* DONT_TOUCH = "true" *)
module Optimized_MUX(
    input  wire [3:0] D,
    input  wire [1:0] S,
    output wire       Y
    );
    
    // --- FIX: Define internal wires for the select bits ---
    wire S0 = S[0];
    wire S1 = S[1];

    //--------FOR LUT DEPTH 1--------------
    //--------AND LUTS--------------------
    //-- INDEX FORMAT -> I2(S1) I1(S0) I0(D) --------
    wire and1, and2, and3, and4;
    
    // Case 00: S1=0, S0=0, D[0]=1 -> Index 001 (1) -> Bit 1 is High
    (* DONT_TOUCH = "true" *)
    LUT3 #(.INIT(8'b00000010)) lut_and1(
        .I0(D[0]), .I1(S0), .I2(S1), .O(and1)
    );
    
    // Case 01: S1=0, S0=1, D[1]=1 -> Index 011 (3) -> Bit 3 is High
    (* DONT_TOUCH = "true" *)
     LUT3 #(.INIT(8'b00001000)) lut_and2(
        .I0(D[1]), .I1(S0), .I2(S1), .O(and2)
    );
    
    // Case 10: S1=1, S0=0, D[2]=1 -> Index 101 (5) -> Bit 5 is High
    (* DONT_TOUCH = "true" *)
     LUT3 #(.INIT(8'b00100000)) lut_and3(
        .I0(D[2]), .I1(S0), .I2(S1), .O(and3)
    );
    
    // Case 11: S1=1, S0=1, D[3]=1 -> Index 111 (7) -> Bit 7 is High
    (* DONT_TOUCH = "true" *)
     LUT3 #(.INIT(8'b10000000)) lut_and4(
        .I0(D[3]), .I1(S0), .I2(S1), .O(and4)
    );
    
  //-----------LUT DEPTH 2--------------
  //-----------OR LUTS------------------
  // INIT 4'b1110 is correct for OR gate (11 | 10 | 01 = 1, 00 = 0)
  wire or1, or2;
  
  (* DONT_TOUCH = "true" *)
   LUT2 #(.INIT(4'b1110)) lut_or1(
    .I0(and1), .I1(and2), .O(or1)
    );
    
    (* DONT_TOUCH = "true" *)
    LUT2 #(.INIT(4'b1110)) lut_or2(
    .I0(and3), .I1(and4), .O(or2)
    );
    
    
  //-----------LUT DEPTH 3--------------
  //-----------OUTPUT NODE--------------
   LUT2 #(.INIT(4'b1110)) lut_or3(
    .I0(or1), .I1(or2), .O(Y)
    );
  
endmodule
