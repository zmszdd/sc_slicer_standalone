; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun is_closing_force_exercise () Bool)
(declare-fun move_flag () Bool)
(declare-fun token_delta_correct () Bool)
(assert
 (= is_closing_force_exercise is_closing_force_exercise))
(assert
 (= move_flag move_flag))
(assert
 (= token_delta_correct token_delta_correct))
(define-fun report_preconditions () Bool is_closing_force_exercise)
(define-fun report_safety () Bool (=> is_closing_force_exercise (and (= move_flag false) token_delta_correct)))
(define-fun report_effects () Bool (and is_closing_force_exercise
     (not (and (= move_flag false) token_delta_correct))))
