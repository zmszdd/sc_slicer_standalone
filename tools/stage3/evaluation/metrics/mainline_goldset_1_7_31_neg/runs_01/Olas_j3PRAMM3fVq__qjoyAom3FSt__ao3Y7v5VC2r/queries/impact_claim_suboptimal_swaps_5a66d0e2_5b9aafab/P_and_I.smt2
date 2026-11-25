; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c118b3980_path_admin_settable () Bool)
(declare-fun c118b3980_second_token_address () ReportAddress)
(declare-fun c118b3980_suboptimal_swap_occurred () Bool)
(declare-fun c118b3980_swap_path_fixed_second_to_olas () Bool)
(declare-fun c118b3980_swap_path_input_token () ReportAddress)
(assert
 (= c118b3980_path_admin_settable c118b3980_path_admin_settable))
(assert
 (= c118b3980_second_token_address c118b3980_second_token_address))
(assert
 (= c118b3980_suboptimal_swap_occurred c118b3980_suboptimal_swap_occurred))
(assert
 (= c118b3980_swap_path_fixed_second_to_olas c118b3980_swap_path_fixed_second_to_olas))
(assert
 (= c118b3980_swap_path_input_token c118b3980_swap_path_input_token))
(define-fun report_preconditions () Bool (and c118b3980_swap_path_fixed_second_to_olas
     (not c118b3980_path_admin_settable)))
(define-fun report_safety () Bool (= c118b3980_swap_path_input_token c118b3980_second_token_address))
(define-fun report_effects () Bool (and (not c118b3980_path_admin_settable)
     (not (= c118b3980_swap_path_input_token c118b3980_second_token_address))
     c118b3980_suboptimal_swap_occurred))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
