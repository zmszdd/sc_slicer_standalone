; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun c62dc143c_caller_is_not_holder () Bool)
(declare-fun c62dc143c_debited_holder () ReportAddress)
(declare-fun c62dc143c_emitted_from () ReportAddress)
(declare-fun c62dc143c_log_misrepresents_sender () Bool)
(assert
 (= c62dc143c_caller_is_not_holder c62dc143c_caller_is_not_holder))
(assert
 (= c62dc143c_debited_holder c62dc143c_debited_holder))
(assert
 (= c62dc143c_emitted_from c62dc143c_emitted_from))
(assert
 (= c62dc143c_log_misrepresents_sender c62dc143c_log_misrepresents_sender))
(define-fun report_preconditions () Bool c62dc143c_caller_is_not_holder)
(define-fun report_safety () Bool (=> c62dc143c_caller_is_not_holder
    (and (= c62dc143c_emitted_from c62dc143c_debited_holder)
         (not c62dc143c_log_misrepresents_sender))))
(define-fun report_effects () Bool (and c62dc143c_caller_is_not_holder
     (not (and (= c62dc143c_emitted_from c62dc143c_debited_holder)
               (not c62dc143c_log_misrepresents_sender)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
