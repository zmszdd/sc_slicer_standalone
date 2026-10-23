; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb2f82172_le_result_operand_order_1 () Bool)
(declare-fun cb2f82172_le_result_operand_order_2 () Bool)
(declare-fun cb2f82172_operands_differ_in_bit_representation () Bool)
(declare-fun cb2f82172_operands_have_equal_exponents () Bool)
(declare-fun cb2f82172_operands_mathematically_equal () Bool)
(assert
 (= cb2f82172_le_result_operand_order_1 cb2f82172_le_result_operand_order_1))
(assert
 (= cb2f82172_le_result_operand_order_2 cb2f82172_le_result_operand_order_2))
(assert
 (= cb2f82172_operands_differ_in_bit_representation cb2f82172_operands_differ_in_bit_representation))
(assert
 (= cb2f82172_operands_have_equal_exponents cb2f82172_operands_have_equal_exponents))
(assert
 (= cb2f82172_operands_mathematically_equal cb2f82172_operands_mathematically_equal))
(define-fun report_preconditions () Bool (and cb2f82172_operands_have_equal_exponents
     cb2f82172_operands_mathematically_equal
     cb2f82172_operands_differ_in_bit_representation))
(define-fun report_safety () Bool (=> (and cb2f82172_operands_have_equal_exponents
         cb2f82172_operands_mathematically_equal
         cb2f82172_operands_differ_in_bit_representation)
    (= cb2f82172_le_result_operand_order_1 cb2f82172_le_result_operand_order_2)))
(define-fun report_effects () Bool (and cb2f82172_operands_have_equal_exponents
     cb2f82172_operands_mathematically_equal
     cb2f82172_operands_differ_in_bit_representation
     (not (= cb2f82172_le_result_operand_order_1
             cb2f82172_le_result_operand_order_2))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
