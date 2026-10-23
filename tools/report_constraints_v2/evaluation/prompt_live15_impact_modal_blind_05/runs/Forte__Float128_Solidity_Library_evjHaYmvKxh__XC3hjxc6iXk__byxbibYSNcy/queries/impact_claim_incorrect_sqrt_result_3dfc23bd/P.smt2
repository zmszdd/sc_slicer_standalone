; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c31590a18_max_l_digit_number () Int)
(declare-fun c31590a18_number_is_large () Bool)
(declare-fun c31590a18_rman_before () Int)
(declare-fun c31590a18_sqrt_result_correct () Bool)
(assert
 (= c31590a18_max_l_digit_number c31590a18_max_l_digit_number))
(assert
 (= c31590a18_number_is_large c31590a18_number_is_large))
(assert
 (= c31590a18_rman_before c31590a18_rman_before))
(assert
 (= c31590a18_sqrt_result_correct c31590a18_sqrt_result_correct))
(define-fun report_preconditions () Bool (and c31590a18_number_is_large
     (> c31590a18_rman_before c31590a18_max_l_digit_number)))
(define-fun report_safety () Bool (=> (and c31590a18_number_is_large
         (> c31590a18_rman_before c31590a18_max_l_digit_number))
    c31590a18_sqrt_result_correct))
(define-fun report_effects () Bool (and c31590a18_number_is_large
     (> c31590a18_rman_before c31590a18_max_l_digit_number)
     (not c31590a18_sqrt_result_correct)))
(assert report_preconditions)
(check-sat)
(get-model)
