; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6ce21310_executed_outside_window () Bool)
(declare-fun c6ce21310_op_is_valid_77byte_signed () Bool)
(declare-fun c6ce21310_relayer_holds_op () Bool)
(declare-fun c6ce21310_suffix_excluded_from_hash () Bool)
(assert
 (= c6ce21310_executed_outside_window c6ce21310_executed_outside_window))
(assert
 (= c6ce21310_op_is_valid_77byte_signed c6ce21310_op_is_valid_77byte_signed))
(assert
 (= c6ce21310_relayer_holds_op c6ce21310_relayer_holds_op))
(assert
 (= c6ce21310_suffix_excluded_from_hash c6ce21310_suffix_excluded_from_hash))
(define-fun report_preconditions () Bool (and c6ce21310_op_is_valid_77byte_signed
     c6ce21310_relayer_holds_op
     c6ce21310_suffix_excluded_from_hash))
(define-fun report_safety () Bool (=> (and c6ce21310_op_is_valid_77byte_signed
         c6ce21310_relayer_holds_op
         c6ce21310_suffix_excluded_from_hash)
    (not c6ce21310_executed_outside_window)))
(define-fun report_effects () Bool (and c6ce21310_op_is_valid_77byte_signed
     c6ce21310_relayer_holds_op
     c6ce21310_suffix_excluded_from_hash
     (not (not c6ce21310_executed_outside_window))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
