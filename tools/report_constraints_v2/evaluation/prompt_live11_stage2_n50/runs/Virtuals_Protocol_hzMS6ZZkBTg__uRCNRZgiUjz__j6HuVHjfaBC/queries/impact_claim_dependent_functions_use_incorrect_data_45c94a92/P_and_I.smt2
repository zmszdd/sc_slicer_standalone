; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun caeae4e11_dependent_ratings_incorrect () Bool)
(declare-fun caeae4e11_elob_should_decrease () Bool)
(declare-fun caeae4e11_elob_should_increase () Bool)
(declare-fun caeae4e11_negative_flag () Bool)
(declare-fun caeae4e11_rating_change_obtained () Bool)
(assert
 (= caeae4e11_dependent_ratings_incorrect caeae4e11_dependent_ratings_incorrect))
(assert
 (= caeae4e11_elob_should_decrease caeae4e11_elob_should_decrease))
(assert
 (= caeae4e11_elob_should_increase caeae4e11_elob_should_increase))
(assert
 (= caeae4e11_negative_flag caeae4e11_negative_flag))
(assert
 (= caeae4e11_rating_change_obtained caeae4e11_rating_change_obtained))
(define-fun report_preconditions () Bool (and caeae4e11_rating_change_obtained
     (= caeae4e11_elob_should_decrease caeae4e11_negative_flag)
     (distinct caeae4e11_elob_should_increase caeae4e11_negative_flag)))
(define-fun report_safety () Bool (=> (and caeae4e11_rating_change_obtained
         (= caeae4e11_elob_should_decrease caeae4e11_negative_flag)
         (distinct caeae4e11_elob_should_increase caeae4e11_negative_flag))
    (= caeae4e11_dependent_ratings_incorrect false)))
(define-fun report_effects () Bool (and caeae4e11_rating_change_obtained
     (= caeae4e11_elob_should_decrease caeae4e11_negative_flag)
     (distinct caeae4e11_elob_should_increase caeae4e11_negative_flag)
     (not (= caeae4e11_dependent_ratings_incorrect false))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
